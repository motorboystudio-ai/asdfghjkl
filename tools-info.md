# Tooling Requirements for ECU/SmartKey Protocol Deep Analysis

This document outlines the essential, minimalist toolset required for deep analysis and reverse engineering of the Honda ECU/SmartKey communication protocol, categorized by platform.

## 1. Windows Tools (Focus: Reverse Engineering, Debugging & Monitoring)
These tools are essential for analyzing the original .exe file and its interactions with the hardware drivers.

- **[x64dbg](https://x64dbg.com/):** Professional-grade debugger for analyzing logic, memory, and function calls (specifically interactions with `ftd2xx.dll`).
- **[Process Monitor (Sysinternals)](https://learn.microsoft.com/en-us/sysinternals/downloads/procmon):** Used to monitor real-time file system, registry, and process activity of the original software.
- **[HxD](https://mh-nexus.de/en/hxd.htm):** Lightweight, fast hex editor for analyzing binary data within `.dat` files and raw traffic logs.
- **[API Monitor](http://www.rohitab.com/apimonitor):** Used to intercept and monitor Windows API and DLL function calls, crucial for understanding how the software commands the FTDI hardware.

## 2. Kali Linux / Linux Tools (Focus: Protocol, Traffic & Dynamic Analysis)
These tools are ideal for protocol analysis, decompilation, and dynamic instrumentation.

- **[Ghidra](https://ghidra-sre.org/):** Powerful software reverse engineering suite (SRE) for static analysis and decompilation of binaries.
- **[Wireshark](https://www.wireshark.org/):** Essential for capturing and analyzing communication traffic.
- **[Frida](https://frida.re/):** Dynamic instrumentation toolkit for hooking functions at runtime without modifying the binary.
- **[socat](http://www.dest-unreach.org/socat/) / [minicom](https://linux.die.net/man/1/minicom):** Robust command-line tools for testing and interacting with Serial/USB communication.

---

## 3. Hardware Analysis Tools (Protocol Inspection)
Tools to capture raw communication between the original software/hardware and the ECU.

- **Logic Analyzer (e.g., 8-channel, 24MHz):** Real-time signal analysis (Baud rate, waveform inspection).
- **Custom K-Line Sniffer:** A circuit utilizing a transceiver chip (e.g., L9637D or MC33660) to convert K-Line signals to a readable TTL level for the Logic Analyzer.
- **Saleae Logic Software:** The industry standard for visualizing and decoding protocol data from Logic Analyzers.

---

## Minimalist Workflow
1.  **Windows:** Use **x64dbg** and **API Monitor** to identify communication patterns through `ftd2xx.dll`.
2.  **Linux:** Use **Ghidra** to perform static analysis on identified functions to understand the underlying protocol algorithms.
3.  **Hardware:** Use **Logic Analyzer + Sniffer** to capture raw traffic to validate findings.
4.  **Verification:** Use **socat/minicom** on Linux to simulate commands and verify protocol understanding.
