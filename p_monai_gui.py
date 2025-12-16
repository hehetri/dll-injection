"""Simple GUI to browse ``p_monai`` data from text or encoded binary files."""
from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

HEADER_PREFIX = b"\xfe\xff\xff\xff"
DEFAULT_BIN_PATH = Path("dungeon/p_monai.bin")
DEFAULT_TXT_PATH = Path("output/dungeon/p_monai.txt")


def xor_decode(data: bytes) -> bytes:
    """Return ``data`` XOR-ed with ``0xFF``."""

    return bytes(b ^ 0xFF for b in data)


def strip_header(decoded: bytes) -> bytes:
    """Remove the leading 8-byte header when present."""

    if len(decoded) >= 8 and decoded.startswith(HEADER_PREFIX):
        return decoded[8:]
    return decoded


def strip_padding(decoded: bytes) -> bytes:
    """Trim trailing ``0xFF`` padding bytes."""

    end = len(decoded)
    while end > 0 and decoded[end - 1] == 0xFF:
        end -= 1
    return decoded[:end]


def load_p_monai_text(path: Path) -> str:
    """Load ``p_monai`` data from ``path`` and return it as text."""

    raw_bytes = path.read_bytes()
    if path.suffix.lower() == ".bin":
        raw_bytes = strip_padding(strip_header(xor_decode(raw_bytes)))
    return raw_bytes.decode("utf-8", errors="replace")


def pick_default_path() -> Path:
    """Choose a sensible default input path for ``p_monai`` data."""

    if DEFAULT_BIN_PATH.exists():
        return DEFAULT_BIN_PATH
    if DEFAULT_TXT_PATH.exists():
        return DEFAULT_TXT_PATH
    raise FileNotFoundError(
        "Could not find default p_monai sources. Provide a file explicitly."
    )


def parse_table(text: str) -> tuple[list[str], list[list[str]]]:
    """Parse the text into column names and rows for display.

    The header is taken from the first line containing the word ``INDEX``.
    Comment lines starting with ``;`` are ignored for the body.
    """

    lines = [line for line in text.splitlines() if line.strip()]
    header_index = next(
        (i for i, line in enumerate(lines) if "INDEX" in line.upper()), None
    )
    if header_index is None:
        return ["Line"], [[line] for line in lines]

    header_line = lines[header_index].lstrip("; ")
    columns = [col.strip() or f"col{i+1}" for i, col in enumerate(header_line.split("\t"))]
    rows: list[list[str]] = []
    for line in lines[header_index + 1 :]:
        if line.lstrip().startswith(";"):
            continue
        values = line.split("\t")
        if len(values) < len(columns):
            values.extend([""] * (len(columns) - len(values)))
        elif len(values) > len(columns):
            values = values[: len(columns)]
        rows.append(values)
    return columns, rows


class PMonaiGUI(tk.Frame):
    """Tkinter-based browser for ``p_monai`` data tables."""

    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master)
        self.master.title("p_monai Viewer")
        self.pack(fill=tk.BOTH, expand=True)
        self.current_path: Path | None = None
        self.create_widgets()
        try:
            default_path = pick_default_path()
        except FileNotFoundError:
            default_path = None
        if default_path:
            self.load_file(default_path)

    def create_widgets(self) -> None:
        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(control_frame, text="Arquivo:").pack(side=tk.LEFT)
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(control_frame, textvariable=self.path_var, width=60)
        self.path_entry.pack(side=tk.LEFT, padx=(4, 4), fill=tk.X, expand=True)

        ttk.Button(
            control_frame, text="Abrir...", command=self.choose_file
        ).pack(side=tk.LEFT)
        ttk.Button(
            control_frame, text="Salvar texto...", command=self.save_text
        ).pack(side=tk.LEFT, padx=(4, 0))

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self.tree = ttk.Treeview(tree_frame, show="headings")
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

    def choose_file(self) -> None:
        path_str = filedialog.askopenfilename(
            title="Selecione p_monai.bin ou p_monai.txt",
            filetypes=[
                ("p_monai files", "p_monai.*"),
                ("Arquivos binários", "*.bin"),
                ("Arquivos de texto", "*.txt"),
                ("Todos", "*.*"),
            ],
        )
        if path_str:
            self.load_file(Path(path_str))

    def save_text(self) -> None:
        if self.current_path is None:
            messagebox.showinfo("Salvar", "Nenhum arquivo carregado ainda.")
            return
        text = load_p_monai_text(self.current_path)
        dest = filedialog.asksaveasfilename(
            title="Salvar texto decodificado",
            defaultextension=".txt",
            filetypes=[("Arquivo de texto", "*.txt"), ("Todos", "*.*")],
        )
        if dest:
            Path(dest).write_text(text, encoding="utf-8")
            messagebox.showinfo("Salvar", f"Texto salvo em {dest}")

    def clear_table(self) -> None:
        for col in self.tree["columns"]:
            self.tree.heading(col, text="")
            self.tree.column(col, width=80)
        self.tree.delete(*self.tree.get_children())

    def populate_table(self, columns: list[str], rows: list[list[str]]) -> None:
        self.clear_table()
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        for row in rows:
            self.tree.insert("", tk.END, values=row)

    def load_file(self, path: Path) -> None:
        try:
            text = load_p_monai_text(path)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Erro", f"Não foi possível ler o arquivo: {exc}")
            return

        columns, rows = parse_table(text)
        if not rows:
            messagebox.showinfo("Aviso", "Nenhuma linha de dados encontrada.")
        self.populate_table(columns, rows)
        self.path_var.set(str(path))
        self.current_path = path


def main() -> None:
    root = tk.Tk()
    root.geometry("1200x700")
    PMonaiGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
