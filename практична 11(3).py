import math
import re
import tkinter as tk
from tkinter import messagebox
from abc import ABC, abstractmethod


class Expression(ABC):
    @abstractmethod
    def evaluate(self, ctx: dict) -> float: pass

    @abstractmethod
    def derivative(self, var: str) -> "Expression": pass


class Number(Expression):
    def __init__(self, val: float): self.val = float(val)
    def evaluate(self, ctx: dict) -> float: return self.val
    def derivative(self, var: str) -> Expression: return Number(0.0)


class Variable(Expression):
    def __init__(self, name: str): self.name = name
    def evaluate(self, ctx: dict) -> float: return float(ctx[self.name])
    def derivative(self, var: str) -> Expression: return Number(1.0 if self.name == var else 0.0)


class Add(Expression):
    def __init__(self, l: Expression, r: Expression): self.l, self.r = l, r
    def evaluate(self, ctx: dict) -> float: return self.l.evaluate(ctx) + self.r.evaluate(ctx)
    def derivative(self, var: str) -> Expression: return Add(self.l.derivative(var), self.r.derivative(var))


class Sub(Expression):
    def __init__(self, l: Expression, r: Expression): self.l, self.r = l, r
    def evaluate(self, ctx: dict) -> float: return self.l.evaluate(ctx) - self.r.evaluate(ctx)
    def derivative(self, var: str) -> Expression: return Sub(self.l.derivative(var), self.r.derivative(var))


class Mult(Expression):
    def __init__(self, l: Expression, r: Expression): self.l, self.r = l, r
    def evaluate(self, ctx: dict) -> float: return self.l.evaluate(ctx) * self.r.evaluate(ctx)
    def derivative(self, var: str) -> Expression:
        return Add(Mult(self.l.derivative(var), self.r), Mult(self.l, self.r.derivative(var)))


class Div(Expression):
    def __init__(self, l: Expression, r: Expression): self.l, self.r = l, r
    def evaluate(self, ctx: dict) -> float: return self.l.evaluate(ctx) / self.r.evaluate(ctx)
    def derivative(self, var: str) -> Expression:
        num = Sub(Mult(self.l.derivative(var), self.r), Mult(self.l, self.r.derivative(var)))
        return Div(num, Mult(self.r, self.r))


# --- Похідні класи Sin та Cos ---
class Sin(Expression):
    def __init__(self, arg: Expression):
        self.arg = arg

    def evaluate(self, ctx: dict) -> float:
        return math.sin(self.arg.evaluate(ctx))

    def derivative(self, var: str) -> Expression:
        # (sin(u))' = cos(u) * u'
        return Mult(Cos(self.arg), self.arg.derivative(var))


class Cos(Expression):
    def __init__(self, arg: Expression):
        self.arg = arg

    def evaluate(self, ctx: dict) -> float:
        return math.cos(self.arg.evaluate(ctx))

    def derivative(self, var: str) -> Expression:
        # (cos(u))' = (0 - sin(u)) * u'
        return Mult(Sub(Number(0.0), Sin(self.arg)), self.arg.derivative(var))


def form(expr_str: str) -> Expression:
    """Оновлена функція form() з підтримкою sin() та cos()."""
    tokens = re.findall(r"\d+(?:\.\d+)?|[a-zA-Z_]\w*|[+\-*/()]", expr_str)
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
        while pos < len(tokens) and tokens[pos] in ("*", "/"):
            op = tokens[pos]; pos += 1
            node = Mult(node, parse_atom()) if op == "*" else Div(node, parse_atom())
        return node

    def parse_atom():
        nonlocal pos
        tok = tokens[pos]; pos += 1
        if tok == "(":
            node = parse_add()
            pos += 1
            return node
        if tok in ("sin", "cos"):
            pos += 1  # пропускаємо '('
            arg = parse_add()
            pos += 1  # пропускаємо ')'
            return Sin(arg) if tok == "sin" else Cos(arg)
        if re.fullmatch(r"\d+(?:\.\d+)?", tok):
            return Number(float(tok))
        return Variable(tok)

    return parse_add()


class Task3App:
    def __init__(self, root):
        self.root = root
        self.root.title("Завдання 3: Тригонометрія sin() і cos()")
        self.root.geometry("460x260")

        tk.Label(root, text="Вираз S(t):").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.edit_expr = tk.Entry(root, width=35)
        self.edit_expr.insert(0, "10 * sin(2 * t) + 5 * cos(t)")
        self.edit_expr.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(root, text="Час t (рад):").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.edit_t = tk.Entry(root, width=35)
        self.edit_t.insert(0, "1.5708")
        self.edit_t.grid(row=1, column=1, padx=10, pady=5)

        tk.Button(root, text="Обчислити S(t), S'(t), S''(t)", bg="#fff2cc", command=self.calculate).grid(
            row=2, column=0, columnspan=2, pady=10
        )

        labels = ["Значення S(t):", "Перша похідна S'(t):", "Друга похідна S''(t):"]
        self.outputs = []
        for i, text in enumerate(labels):
            tk.Label(root, text=text).grid(row=3 + i, column=0, sticky="w", padx=10, pady=3)
            ent = tk.Entry(root, width=35)
            ent.grid(row=3 + i, column=1, padx=10, pady=3)
            self.outputs.append(ent)

    def calculate(self):
        try:
            ctx = {"t": float(self.edit_t.get().replace(",", "."))}
            s_tree = form(self.edit_expr.get())
            v_tree = s_tree.derivative("t")
            a_tree = v_tree.derivative("t")

            for ent, tree in zip(self.outputs, [s_tree, v_tree, a_tree]):
                ent.delete(0, tk.END)
                ent.insert(0, f"{tree.evaluate(ctx):.6f}")
        except Exception as e:
            messagebox.showerror("Помилка", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    Task3App(root)
    root.mainloop()