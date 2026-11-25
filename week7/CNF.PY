from typing import Set, List, Union, Tuple
from dataclasses import dataclass
from itertools import product

# ============ AST Representation ============

@dataclass(frozen=True)
class Var:
    name: str
    def __repr__(self): return self.name

@dataclass(frozen=True)
class Not:
    operand: 'Expr'
    def __repr__(self): return f"¬{self.operand}"

@dataclass(frozen=True)
class And:
    left: 'Expr'
    right: 'Expr'
    def __repr__(self): return f"({self.left} ∧ {self.right})"

@dataclass(frozen=True)
class Or:
    left: 'Expr'
    right: 'Expr'
    def __repr__(self): return f"({self.left} ∨ {self.right})"

@dataclass(frozen=True)
class Implies:
    left: 'Expr'
    right: 'Expr'
    def __repr__(self): return f"({self.left} → {self.right})"

@dataclass(frozen=True)
class Iff:
    left: 'Expr'
    right: 'Expr'
    def __repr__(self): return f"({self.left} ↔ {self.right})"

Expr = Union[Var, Not, And, Or, Implies, Iff]


# ============ Helper Functions ============

def eliminate_iff(expr: Expr) -> Expr:
    """Remove biconditionals: A ↔ B  ==>  (A → B) ∧ (B → A)"""
    if isinstance(expr, Var):
        return expr
    if isinstance(expr, Not):
        return Not(eliminate_iff(expr.operand))
    if isinstance(expr, And):
        return And(eliminate_iff(expr.left), eliminate_iff(expr.right))
    if isinstance(expr, Or):
        return Or(eliminate_iff(expr.left), eliminate_iff(expr.right))
    if isinstance(expr, Implies):
        return Implies(eliminate_iff(expr.left), eliminate_iff(expr.right))
    if isinstance(expr, Iff):
        l = eliminate_iff(expr.left)
        r = eliminate_iff(expr.right)
        return And(Implies(l, r), Implies(r, l))
    raise TypeError(f"Unknown expression: {expr}")


def eliminate_implies(expr: Expr) -> Expr:
    """Remove implications: A → B  ==>  ¬A ∨ B"""
    if isinstance(expr, Var):
        return expr
    if isinstance(expr, Not):
        return Not(eliminate_implies(expr.operand))
    if isinstance(expr, And):
        return And(eliminate_implies(expr.left), eliminate_implies(expr.right))
    if isinstance(expr, Or):
        return Or(eliminate_implies(expr.left), eliminate_implies(expr.right))
    if isinstance(expr, Implies):
        return Or(Not(eliminate_implies(expr.left)), eliminate_implies(expr.right))
    raise TypeError(f"Unexpected expression: {expr}")


def push_negations(expr: Expr) -> Expr:
    """Push negations inward using De Morgan's laws & double-negation."""
    if isinstance(expr, Var):
        return expr
    if isinstance(expr, Not):
        inner = expr.operand
        if isinstance(inner, Var):
            return expr                       # ¬x is already literal
        if isinstance(inner, Not):
            return push_negations(inner.operand)   # ¬¬A → A
        if isinstance(inner, And):
            # ¬(A ∧ B) → ¬A ∨ ¬B
            return Or(push_negations(Not(inner.left)),
                      push_negations(Not(inner.right)))
        if isinstance(inner, Or):
            # ¬(A ∨ B) → ¬A ∧ ¬B
            return And(push_negations(Not(inner.left)),
                       push_negations(Not(inner.right)))
        raise TypeError(f"Bad inner of Not: {inner}")
    if isinstance(expr, And):
        return And(push_negations(expr.left), push_negations(expr.right))
    if isinstance(expr, Or):
        return Or(push_negations(expr.left), push_negations(expr.right))
    raise TypeError(f"Unexpected expression: {expr}")


def distribute(expr: Expr) -> Expr:
    """
    Distribute OR over AND so the formula becomes a conjunction of clauses.
    A ∨ (B ∧ C)  ==>  (A ∨ B) ∧ (A ∨ C)
    (B ∧ C) ∨ A  ==>  (B ∨ A) ∧ (C ∨ A)
    """
    if isinstance(expr, (Var, Not)):
        return expr

    if isinstance(expr, And):
        return And(distribute(expr.left), distribute(expr.right))

    if isinstance(expr, Or):
        left = distribute(expr.left)
        right = distribute(expr.right)

        # (A ∧ B) ∨ C  ==>  (A ∨ C) ∧ (B ∨ C)
        if isinstance(left, And):
            return And(
                distribute(Or(left.left, right)),
                distribute(Or(left.right, right)),
            )
        # C ∨ (A ∧ B)  ==>  (C ∨ A) ∧ (C ∨ B)
        if isinstance(right, And):
            return And(
                distribute(Or(left, right.left)),
                distribute(Or(left, right.right)),
            )
        return Or(left, right)

    raise TypeError(f"Unexpected expression: {expr}")


def to_cnf(expr: Expr) -> Expr:
    """Pipeline: eliminate ↔, eliminate →, push ¬, distribute."""
    return distribute(push_negations(eliminate_implies(eliminate_iff(expr))))


# ============ Clause Extraction & Utility ============

def collect_clauses(expr: Expr) -> List[List[Tuple[str, bool]]]:
    """
    Turn a CNF expression into a list of clauses.
    Each clause is a list of literals (name, is_negated).
    """
    clauses = []
    def walk(e: Expr, current: list):
        if isinstance(e, Var):
            current.append((e.name, False))
        elif isinstance(e, Not):
            if not isinstance(e.operand, Var):
                raise ValueError("CNF literal expected under Not")
            current.append((e.operand.name, True))
        elif isinstance(e, Or):
            walk(e.left, current)
            walk(e.right, current)
        elif isinstance(e, And):
            walk(e.left, current)
            clauses.append(current)
            walk(e.right, current)
            # append right-side clause after walking left
            # (handled via recursive calls above)
        else:
            raise TypeError(f"Bad CNF node: {e}")

    # Use a simpler split-based approach instead:
    def split(e: Expr) -> List[List[Tuple[str, bool]]]:
        if isinstance(e, And):
            return split(e.left) + split(e.right)
        # e is a clause (Or-tree of literals)
        lits = []
        def gather(x: Expr):
            if isinstance(x, Var):
                lits.append((x.name, False))
            elif isinstance(x, Not) and isinstance(x.operand, Var):
                lits.append((x.operand.name, True))
            elif isinstance(x, Or):
                gather(x.left); gather(x.right)
            else:
                raise TypeError(f"Bad clause node: {x}")
        gather(e)
        return [lits]

    return split(expr)


def clause_to_str(clause: List[Tuple[str, bool]]) -> str:
    return "(" + " ∨ ".join(
        ("" if neg else "") + name for name, neg in clause
    ) + ")"


def cnf_to_string(expr: Expr) -> str:
    clauses = collect_clauses(expr)
    return " ∧ ".join(clause_to_str(c) for c in clauses)


def satisfiable(expr: Expr) -> bool:
    """Brute-force SAT check on the CNF (small formulas only)."""
    clauses = collect_clauses(expr)
    vars_ = sorted({name for c in clauses for name, _ in c})
    if not vars_:
        return all(len(c) == 0 for c in []) or True
    for values in product([False, True], repeat=len(vars_)):
        assign = dict(zip(vars_, values))
        if all(
            any((lit not in assign) is False and
                (assign[lit] != neg)  # satisfied if var matches polarity
                for lit, neg in c)
            for c in clauses
        ):
            return True
    return False


# ============ Demo ============

if __name__ == "__main__":
    # Example 1: (P → Q) ∧ ¬R  ... wait, let's build something richer
    # Formula: (P ↔ Q) → (R ∧ S)
    P, Q, R, S = Var("P"), Var("Q"), Var("R"), Var("S")
    formula = Implies(Iff(P, Q), And(R, S))
    print("Original :", formula)
    print("CNF      :", cnf_to_string(to_cnf(formula)))
