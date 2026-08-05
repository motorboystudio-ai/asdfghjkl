from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Button, Static, Label
from textual.containers import Container, Horizontal, Vertical

class HondaReaderCLI(App):
    CSS = """
    Screen { layout: horizontal; }
    #sidebar { width: 30; background: $surface; border-right: vkey $accent; padding: 1; }
    #main { layout: vertical; padding: 1; }
    .button-group { margin-top: 1; dock: bottom; }
    Button { width: 100%; margin: 1 0; }
    DataTable { height: 80%; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="sidebar"):
            yield Label("MENU", classes="title")
            yield Button("Database KEIHIN", id="btn-keihin")
            yield Button("Database SHINDENGEN", id="btn-shindengen")
            yield Button("Live Data", id="btn-live")
        
        with Container(id="main"):
            yield Label("Database View", id="view-title")
            table = DataTable()
            table.add_columns("Type Motor", "Part Number", "ECM ID", "Size")
            yield table
            with Horizontal(classes="button-group"):
                yield Button("Read ID", variant="primary")
                yield Button("Write", variant="warning")
                yield Button("Back", variant="error")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        table = self.query_one(DataTable)
        title = self.query_one("#view-title", Label)
        
        if event.button.id == "btn-keihin":
            title.update("Database KEIHIN")
            table.clear()
            table.add_rows([
                ("BeAT 110 NON ESP", "38770-K25-901", "0101340F01", "48KB"),
                ("GENIO 110 NEW", "30400-K0J-N61", "0104A40F01", "256KB")
            ])
        elif event.button.id == "btn-shindengen":
            title.update("Database SHINDENGEN")
            table.clear()
            table.add_rows([
                ("ADV 160 SMARTKEY", "30400-K0WL-NB1", "01048D0F01", "384KB"),
                ("VARIO 160 SMARTKEY", "30400-K2SA-N02", "01046B0F01", "256KB")
            ])

if __name__ == "__main__":
    app = HondaReaderCLI()
    app.run()
