import math
import re
import tkinter as tk
from tkinter import messagebox
from abc import ABC, abstractmethod


class Expression(ABC):
    @abstractmethod
    def derivative(self, var: str) -> "Expression": pass

    @abstractmethod
    def to_str(self) -> str: pass

    def simplify(self) -> "Expression": return self


class Number(Expression):
    def __init__(self, val: float): self.val = float(val)
    def derivative(self, var: str) -> Expression: return Number(0.0)
    def to_str(self) -> str:
        return str(int(self.val)) if self.val.is_integer() else f"{self.val:g}"


class Variable(Expression):
    def __init__(self, name: str): self.name = name
    def derivative(self, var: str) -> Expression: return Number(1.0 if self.name == var else 0.0)
    def to_str(self) -> str: return self.name


class Add(Expression):
    def __init__(self, l: Expression, r: Expression): self.l, self.r = l, r
    def derivative(self, var: str) -> Expression:
        return Add(self.l.derivative(var), self.r.derivative(var)).simplify()
    def simplify(self) -> Expression:
        l, r = self.l.simplify(), self.r.simplify()
        if isinstance(l, Number) and isinstance(r, Number): return Number(l.val + r.val)
        if isinstance(l, Number) and l.val == 0: return r
        if isinstance(r, Number) and r.val == 0: return l
        return Add(l, r)
    def to_str(self) -> str: return f"({self.l.to_str()} + {self.r.to_str()})"


class Sub(Expression):
    def __init__(self, l: Expression, r: Expression): self.l, self.r = l, r
    def derivative(self, var: str) -> Expression:
        return Sub(self.l.derivative(var), self.r.derivative(var)).simplify()
    def simplify(self) -> Expression:
        l, r = self.l.simplify(), self.r.simplify()
        if isinstance(l, Number) and isinstance(r, Number): return Number(l.val - r.val)
        if isinstance(r, Number) and r.val == 0: return l
        return Sub(l, r)
    def to_str(self) -> str:
        if isinstance(self.l, Number) and self.l.val == 0:
            return f"(-{self.r.to_str()})"
        return f"({self.l.to_str()} - {self.r.to_str()})"


class Mult(Expression):
    def __init__(self, l: Expression, r: Expression): self.l, self.r = l, r
    def derivative(self, var: str) -> Expression:
        return Add(Mult(self.l.derivative(var), self.r), Mult(self.l, self.r.derivative(var))).simplify()
    def simplify(self) -> Expression:
        l, r = self.l.simplify(), self.r.simplify()
        if isinstance(l, Number) and isinstance(r, Number): return Number(l.val * r.val)
        if (isinstance(l, Number) and l.val == 0) or (isinstance(r, Number) and r.val == 0): return Number(0.0)
        if isinstance(l, Number) and l.val == 1: return r
        if isinstance(r, Number) and r.val == 1: return l
        return Mult(l, r)
    def to_str(self) -> str: return f"{self.l.to_str()} * {self.r.to_str()}"


class Sin(Expression):
    def __init__(self, arg: Expression): self.arg = arg
    def derivative(self, var: str) -> Expression:
        return Mult(Cos(self.arg), self.arg.derivative(var)).simplify()
    def simplify(self) -> Expression: return Sin(self.arg.simplify())
    def to_str(self) -> str: return f"sin({self.arg.to_str()})"


class Cos(Expression):
    def __init__(self, arg: Expression): self.arg = arg
    def derivative(self, var: str) -> Expression:
        return Mult(Sub(Number(0.0), Sin(self.arg)), self.arg.derivative(var)).simplify()
    def simplify(self) -> Expression: return Cos(self.arg.simplify())
    def to_str(self) -> str: return f"cos({self.arg.to_str()})"


def form(expr_str: str) -> Expression:
    """Пряма функція: рядок -> деревоподібний граф виразу."""
    tokens = re.findall(r"\d+(?:\.\d+)?|[a-zA-Z_]\w*|[+\-*()]", expr_str)
    pos = 0

    def parse_add():
        nonlocal pos
        node = parse_mul()
        while pos < len(tokens) and tokens[pos] in ("+", "-"):
            op = tokens[pos]; pos += 1
            node = Add(node, parse_mul()) if op == "+" else Sub(node, parse_mul())
        return node

    def parse_mul():
        nonlocal pos
        node = parse_atom()
        while pos < len(tokens) and tokens[pos] == "*":
            pos += 1
            node = Mult(node, parse_atom())
        return node

    def parse_atom():
        nonlocal pos
        tok = tokens[pos]; pos += 1
        if tok == "(":
            node = parse_add(); pos += 1
            return node
        if tok in ("sin", "cos"):
            pos += 1
            arg = parse_add(); pos += 1
            return Sin(arg) if tok == "sin" else Cos(arg)
        if re.fullmatch(r"\d+(?:\.\d+)?", tok):
            return Number(float(tok))
        return Variable(tok)

    return parse_add().simplify()


def unform(tree: Expression) -> str:
    """Функція, обернена до form(): за деревоподібним графом будує рядок виразу."""
    return tree.simplify().to_str()


class Task4App:
    def __init__(self, root):
        self.root = root
        self.root.title("Завдання 4: Аналітична похідна n-го порядку")
        self.root.geometry("540x210")

        tk.Label(root, text="Початковий вираз f(t):").grid(row=0, column=0, sticky="w", padx=10, pady=8)
        self.edit_expr = tk.Entry(root, width=42)
        self.edit_expr.insert(0, "2 * t * t * t + sin(3 * t)")
        self.edit_expr.grid(row=0, column=1, padx=10, pady=8)

        tk.Label(root, text="Порядок похідної (n):").grid(row=1, column=0, sticky="w", padx=10, pady=8)
        self.edit_n = tk.Entry(root, width=10)
        self.edit_n.insert(0, "2")
        self.edit_n.grid(row=1, column=1, sticky="w", padx=10, pady=8)

        tk.Button(root, text="Отримати аналітичний вигляд", bg="#d9ead3", command=self.derive_analytic).grid(
            row=2, column=0, columnspan=2, pady=8
        )

        tk.Label(root, text="Результат f^(n)(t):", font=("Arial", 9, "bold")).grid(row=3, column=0, sticky="w", padx=10, pady=8)
        self.edit_res = tk.Entry(root, width=42, font=("Consolas", 9, "bold"), fg="#0b5394")
        self.edit_res.grid(row=3, column=1, padx=10, pady=8)

    def derive_analytic(self):
        try:
            n = int(self.edit_n.get())
            if n < 0:
                raise ValueError("Порядок похідної має бути >= 0.")

            tree = form(self.edit_expr.get())
            for _ in range(n):
                tree = tree.derivative("t")

            # Виклик функції, оберненої до form()
            analytic_str = unform(tree)

            self.edit_res.delete(0, tk.END)
            self.edit_res.insert(0, analytic_str)
        except Exception as e:
            messagebox.showerror("Помилка", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    Task4App(root)
    root.mainloop()