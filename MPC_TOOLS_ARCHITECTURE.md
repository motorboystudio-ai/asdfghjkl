# MPC Tools: Modern Cross-Platform Architecture Blueprint

## Executive Summary

This document outlines the complete technical blueprint for a cross-platform Flutter application that replaces the legacy Windows ECU diagnostic tool. The solution adheres to clean-room development principles while maintaining 100% legal compliance.

---

## Section 1: Hardware Abstraction Layer (HAL) Design

### 1.1 Recommended Microcontroller Gateway

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **ESP32-S3** | Dual-core, 40MHz SPI, Bluetooth LE, USB-OTG, low cost | Flash encryption requires additional setup | ✅ Primary Choice |
| **STM32H7** | High performance, multiple protocols | Higher cost, steeper learning curve | Alternative for high-volume |
| **RP2040 (Raspberry Pi Pico W)** | Dual-core, WiFi, simple | Bluetooth LE limited, no hardware flow control | Budget alternative |

**Final Recommendation: ESP32-S3 with L9637D transceiver**

### 1.2 Signal Conversion Circuit

**ISO 14230-4 K-Line Implementation:**

```
ECU Pin (K-Line) → L9637D or MC33660 → ESP32 GPIO → TTL Levels → UART
```

**Component Choices:**

| Transceiver | Supply Voltage | ISO 9141-2 Support | Recommendation |
|-------------|----------------|-------------------|----------------|
| L9637D | 5.5V | ✅ | ✅ Recommended |
| MC33660 | 5.5V | ✅ | Also valid |
| TJA1050 | 5.5V | ✅ | Acceptable |

**Key Specifications:**
- **Baud Rate:** 10.4 kbps (Honda standard)
- **Voltage Levels:** K-Line: 0-12V, TTL: 0-3.3V
- **Protection:** Add TVS diode for ESD protection

### 1.3 Communication Protocols Between Flutter and Hardware Gateway

| Protocol | Windows | Android | iOS | Flutter Package | Recommendation |
|----------|---------|---------|-----|-----------------|----------------|
| **Bluetooth LE** | ✅ | ✅ | ✅ | `flutter_reactive_ble` | Mobile primary |
| **USB Serial** | ✅ | ❌ | ❌ | `flutter_libserialport` | Windows primary |
| **WiFi (TCP)** | ✅ | ✅ | ✅ | `socket_io_client` | Universal alternative |
| **OTG Serial** | N/A | ✅ (with OTG) | ❌ | `flutter_libserialport` | Android support |

**Recommended Stack:**

```dart
// Core communication abstraction
abstract class HardwareConnection {
  Future<void> connect();
  Future<void> disconnect();
  Future<List<int>> read(int length);
  Future<void> write(List<int> data);
  Stream<List<int>> onDataReceived();
  ConnectionStatus get status;
}
```

---

## Section 2: Flutter Software Architecture

### 2.1 Clean Architecture Structure

```
lib/
├── main.dart
├── core/
│   ├── constants/
│   ├── utils/
│   └── theme/
├── features/
│   ├── ecu_diagnostic/
│   │   ├── data/
│   │   │   ├── datasources/
│   │   │   ├── models/
│   │   │   └── repositories/
│   │   ├── domain/
│   │   │   ├── entities/
│   │   │   ├── repositories/
│   │   │   └── usecases/
│   │   └── presentation/
│   │       ├── pages/
│   │       ├── widgets/
│   │       └── bloc/
│   └── barcode_scan/
└── injection/
    └── service_locator.dart
```

### 2.2 State Management: Riverpod 2.0+ (Recommended)

**Why Riverpod over Bloc:**
- Simpler boilerplate
- Better testability
- Native async support
- Less verbose for this use case
- First-class support in Flutter DevTools

```dart
// Example: Hardware Connection Provider
final hardwareConnectionProvider = StateNotifierProvider<HardwareConnectionNotifier, ConnectionStatus>((ref) {
  return HardwareConnectionNotifier(ref.read);
});

class HardwareConnectionNotifier extends StateNotifier<ConnectionStatus> {
  HardwareConnectionNotifier(this._read);
  final Reader _read;
  
  Future<void> connect() async {
    final connection = _read.hardwareRepository.connect();
    state = ConnectionStatus.connected();
  }
}
```

### 2.3 Platform-Specific Communication Layer

```dart
class HardwareRepositoryImpl implements HardwareRepository {
  @override
  Future<HardwareConnection> connect() async {
    if (Platform.isAndroid || Platform.isIOS) {
      return BleHardwareConnection();
    } else if (Platform.isWindows) {
      return SerialHardwareConnection();
    }
    throw UnsupportedError('Platform not supported');
  }
}
```

### 2.4 Barcode Scanning Packages

| Platform | Package | Method |
|----------|---------|--------|
| **Android/iOS** | `mlkit_barcode_scanning` | Google ML Kit (no camera permission needed) |
| **Windows** | `mobile_scanner` | Camera access via WebCam |
| **Cross-platform** | `barcode_scan2` | Fallback with camera plugin |

---

## Section 3: Database Design

### 3.1 Isar Schema

```dart
@Collection()
class EcuMapping {
  Id id;
  
  @Index()
  String manufacturer; // 'KEIHIN' or 'SHINDENGEN'
  
  @Index()
  String motorType;
  
  String partNumber;
  String ecmId;
  int startOffset;
  int dataSize;
  String? createdAt;
  String? updatedAt;
  
  // For encryption
  String encryptedPayload;
}
```

### 3.2 Data Encryption Strategy

```dart
class SecureEcuDatabase {
  final Isar _isar;
  final Encrypter _encrypter;
  
  Future<void> insertSecure(EcuMapping mapping) async {
    final json = jsonEncode(mapping.toJson());
    final encrypted = _encrypter.encrypt(json);
    
    final secureMapping = EcuMapping(
      id: Isar.autoIncrement,
      manufacturer: mapping.manufacturer,
      // ... other fields
      encryptedPayload: encrypted.base64,
    );
    
    await _isar.write((txn) => txn.ecuMappings.put(secureMapping));
  }
}
```

**Encryption Key Derivation:**
- Use device-specific key from `local_auth` plugin
- Fallback to secure storage with user PIN
- Never store encryption keys in plaintext

### 3.3 REST API Schema (FastAPI)

```python
# models.py
class EcuMappingBase(BaseModel):
    manufacturer: str
    motor_type: str
    part_number: str
    ecm_id: str
    start_offset: int
    data_size: int

class EcuMapping(EcuMappingBase):
    id: int
    
    class Config:
        orm_mode = True

# endpoints.py
@app.get("/ecu-mappings/")
async def get_mappings(manufacturer: str = None, skip: int = 0, limit: int = 100):
    query = db_session.query(EcuMapping)
    if manufacturer:
        query = query.filter(EcuMapping.manufacturer == manufacturer)
    return query.offset(skip).limit(limit).all()
```

### 3.4 Synchronization Strategy

```dart
class SyncManager {
  Future<void> syncDatabase() async {
    final lastSync = await _getLastSyncTime();
    final remoteMappings = await _apiClient.fetchUpdates(since: lastSync);
    
    await _isar.write((txn) async {
      for (final mapping in remoteMappings) {
        await txn.ecuMappings.putAsync(mapping.toIsarObject());
      }
    });
    
    await _setLastSyncTime(DateTime.now());
  }
}
```

---

## Section 4: Security & Licensing

### 4.1 Device Authentication

```dart
class DeviceLicenseManager {
  Future<String> getDeviceId() async {
    final info = await DeviceInfoPlugin().androidInfo;
    return 'android_${info.androidId}';
  }
  
  Future<bool> validateLicense(String deviceId) async {
    final response = await http.post(
      Uri.parse('$apiUrl/validate-license'),
      body: {'device_id': deviceId},
    );
    return response.statusCode == 200;
  }
}
```

### 4.2 Local Data Protection

```yaml
# pubspec.yaml
dependencies:
  crypto: ^3.0.0
  pointycastle: ^3.7.0
  flutter_secure_storage: ^8.0.0
  local_auth: ^2.0.0
```

### 4.3 Security Best Practices

1. **App Shielding:** Use `flutter_app_locker` to prevent screen capture
2. **Code Obfuscation:** Enable Dart obfuscation in build
3. **Root Detection:** Check for rooted/jailbroken devices
4. **Network Security:** Certificate pinning for API calls

---

## Section 5: Development Roadmap

### Phase 1: Research & Hardware Validation (Weeks 1-2)

| Task | Duration | Deliverable |
|------|----------|-------------|
| Hardware gateway prototype | 5 days | ESP32 + L9637D circuit |
| Protocol reverse engineering | 5 days | Protocol documentation |
| BLE/Serial communication test | 4 days | Working connection demo |

### Phase 2: Core Application Development (Weeks 3-6)

| Task | Duration | Deliverable |
|------|----------|-------------|
| Project scaffolding (Clean Architecture) | 2 days | Git repository structure |
| Database layer (Isar + REST sync) | 4 days | Local storage working |
| Hardware HAL implementation | 6 days | Read/write ECU functionality |
| Authentication & Security | 4 days | License validation working |

### Phase 3: UI/UX Development (Weeks 7-9)

| Task | Duration | Deliverable |
|------|----------|-------------|
| Manufacturer selection flow | 3 days | Working navigation |
| Motorcycle listing | 3 days | Data-driven list |
| ECU ID read functionality | 5 days | Display ECU data |
| Barcode scanning integration | 4 days | Scan → lookup workflow |

### Phase 4: Platform Testing & Deployment (Weeks 10-12)

| Task | Duration | Deliverable |
|------|----------|-------------|
| Windows desktop testing | 3 days | EXE build |
| Android testing | 3 days | APK/AAB build |
| iOS testing | 3 days | IPA build |
| App Store / Play Store setup | 6 days | Published builds |

---

## Flutter Project Structure Template

```
mpc_tools/
├── android/
├── ios/
├── lib/
│   ├── main.dart                 # Entry point
│   ├── core/
│   │   ├── constants/
│   │   ├── theme/
│   │   └── utils/
│   ├── features/
│   │   ├── diagnostic/
│   │   │   ├── presentation/    # UI
│   │   │   ├── domain/          # Business logic
│   │   │   └── data/            # Data sources
│   │   └── barcode/
│   └── injection/               # Dependency injection
├── test/
├── build/
├── pubspec.yaml
└── README.md
```

---

## Recommended Packages (2026 Stable)

```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # State Management
  flutter_riverpod: ^2.4.0
  riverpod_annotation: ^2.3.0
  
  # Database
  isar: ^4.0.0
  isar_flutter_dev_console: ^2.0.0
  
  # Network
  dio: ^5.4.0
  connectivity_plus: ^5.0.0
  
  # Hardware Communication
  flutter_reactive_ble: ^5.2.0
  flutter_libserialport: ^0.5.0
  
  # Barcode Scanning
  mlkit_barcode_scanning: ^0.3.0
  mobile_scanner: ^2.0.0
  
  # Security
  flutter_secure_storage: ^8.0.0
  local_auth: ^2.2.0
  crypto: ^3.0.0
  
  # Device Info
  device_info_plus: ^10.0.0
  package_info_plus: ^7.0.0
```

---

## Cross-Platform Compatibility Matrix

| Feature | Windows | Android | iOS | Implementation |
|---------|---------|---------|-----|----------------|
| FTDI Communication | ✅ USB Serial | ❌ Requires BLE Gateway | ❌ Requires BLE Gateway | Hardware abstraction layer |
| Serial Port Access | ✅ COM Port | ✅ OTG (with adapter) | ❌ | Conditional import |
| BLE Communication | ✅ | ✅ | ✅ | `flutter_reactive_ble` |
| Camera Barcode Scan | ✅ Webcam | ✅ Camera | ✅ Camera | Fallback packages |
| File System Access | ✅ | ✅ Internal | ✅ Documents | `path_provider` |

---

## Legal Compliance Notes

1. **Clean-Room Development:** All code written from scratch without referencing original source
2. **Protocol Interoperability:** Reverse engineering limited to communication protocol discovery only
3. **Independent Implementation:** All algorithms and logic independently re-implemented
4. **No Spoofing:** Original software DRM will not be bypassed or replicated

---

*Document generated: 2026-08-02*