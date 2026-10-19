"""Formal SMT-based constraint verification using Z3 for ContradictPrompt.

Provides mathematical satisfiability proofs for numerical bounds, boolean flags,
and scoped multi-variable constraints, with minimal unsatisfiable core extraction.
"""
from typing import Sequence
import z3
from .models import Instruction, Conflict

class SMTVerifier:
    """Z3-backed SMT constraint solver for prompt requirements."""

    def __init__(self):
        self.solver = z3.Solver()
        self.trackers = {}
        self.variables = {}

    def get_var(self, name: str, var_type: str = 'int') -> z3.ExprRef:
        """Get or create a scoped Z3 variable."""
        key = f"{var_type}:{name}"
        if key not in self.variables:
            if var_type == 'int':
                self.variables[key] = z3.Int(name)
            elif var_type == 'bool':
                self.variables[key] = z3.Bool(name)
            else:
                self.variables[key] = z3.String(name)
        return self.variables[key]

    def verify_numerical_and_boolean(self, instructions: Sequence[Instruction]) -> list[Conflict]:
        """Verify numerical and boolean constraints using Z3 with unsat core tracking.
        
        Constraints belonging to different scopes (e.g. 'summary' vs 'body') operate on
        distinct variables and will not falsely contradict each other.
        """
        conflicts: list[Conflict] = []
        
        # Group by scope and target
        scoped_numeric: dict[tuple[str, str], list[Instruction]] = {}
        scoped_boolean: dict[tuple[str, str], list[Instruction]] = {}

        for ins in instructions:
            scope = ins.scope or 'response'
            target = ins.key or ins.target or 'response'

            if ins.kind == 'numerical' and (ins.lower is not None or ins.upper is not None):
                scoped_numeric.setdefault((scope, target), []).append(ins)
            elif ins.kind == 'formatting' and ins.key in ('json_only', 'bullets', 'markdown', 'xml'):
                scoped_boolean.setdefault((scope, ins.key), []).append(ins)

        # 1. Check numerical constraints per (scope, target)
        for (scope, target), ins_list in scoped_numeric.items():
            if len(ins_list) < 2:
                continue

            s = z3.Solver()
            var = z3.Int(f"num_{scope}_{target}")
            track_map = {}

            # Natural constraint: word/sentence counts cannot be negative
            s.add(var >= 0)

            for idx, ins in enumerate(ins_list):
                tracker = z3.Bool(f"track_{ins.id}_{idx}")
                track_map[str(tracker)] = ins.id

                constraints = []
                if ins.lower is not None and ins.upper is not None:
                    if ins.lower == ins.upper:
                        constraints.append(var == ins.lower)
                    else:
                        constraints.append(z3.And(var >= ins.lower, var <= ins.upper))
                elif ins.lower is not None:
                    constraints.append(var >= ins.lower)
                elif ins.upper is not None:
                    constraints.append(var <= ins.upper)

                if constraints:
                    s.assert_and_track(z3.And(*constraints), tracker)

            if s.check() == z3.unsat:
                core = s.unsat_core()
                conflicting_ids = list(dict.fromkeys(track_map[str(t)] for t in core if str(t) in track_map))
                if len(conflicting_ids) >= 2:
                    explanations = []
                    for cid in conflicting_ids:
                        matching = next((i for i in ins_list if i.id == cid), None)
                        if matching:
                            if matching.lower == matching.upper and matching.lower is not None:
                                explanations.append(f"{matching.id} requires exactly {matching.lower}")
                            elif matching.lower is not None and matching.upper is not None:
                                explanations.append(f"{matching.id} requires between {matching.lower} and {matching.upper}")
                            elif matching.upper is not None:
                                explanations.append(f"{matching.id} requires <= {matching.upper}")
                            elif matching.lower is not None:
                                explanations.append(f"{matching.id} requires >= {matching.lower}")

                    detail = ", whereas ".join(explanations)
                    conflicts.append(Conflict(
                        instruction_ids=conflicting_ids,
                        kind='numerical',
                        explanation=f"SMT Unsatisfiable numerical bounds in {scope} ({target}): {detail}.",
                        severity='hard',
                        source='rule'
                    ))

        # 2. Check boolean constraints per (scope, target)
        for (scope, target), ins_list in scoped_boolean.items():
            if len(ins_list) < 2:
                continue

            s = z3.Solver()
            var = z3.Bool(f"bool_{scope}_{target}")
            track_map = {}

            for idx, ins in enumerate(ins_list):
                tracker = z3.Bool(f"track_{ins.id}_{idx}")
                track_map[str(tracker)] = ins.id

                val = str(ins.value).lower()
                is_true = val in ('true', 'yes', '1', 'only', 'require', 'prefer')
                is_false = val in ('false', 'no', '0', 'forbidden', 'ban', 'deny')

                if is_true:
                    s.assert_and_track(var == True, tracker)
                elif is_false:
                    s.assert_and_track(var == False, tracker)

            if s.check() == z3.unsat:
                core = s.unsat_core()
                conflicting_ids = list(dict.fromkeys(track_map[str(t)] for t in core if str(t) in track_map))
                if len(conflicting_ids) >= 2:
                    conflicts.append(Conflict(
                        instruction_ids=conflicting_ids,
                        kind='formatting',
                        explanation=f"SMT Unsatisfiable contradictory boolean formatting in {scope} for {target}.",
                        severity='hard',
                        source='rule'
                    ))

        # 3. Cross-scope SMT check for total budget vs non-overlapping section minimums
        section_scopes = {ins.scope for ins in instructions if ins.kind == 'numerical' and ins.key == 'word' and ins.scope not in ('response', 'entire', None)}
        if len(section_scopes) >= 2:
            total_ins = [ins for ins in instructions if ins.kind == 'numerical' and ins.key == 'word' and ins.scope in ('response', 'entire', None) and ins.upper is not None]
            for tot in total_ins:
                s_cross = z3.Solver()
                total_var = z3.Int("num_total_words")
                sec_vars = {sec: z3.Int(f"sec_{sec}_words") for sec in section_scopes}
                track_cross = {}

                s_cross.add(total_var >= 0)
                for sv in sec_vars.values():
                    s_cross.add(sv >= 0)
                s_cross.add(total_var >= z3.Sum([sv for sv in sec_vars.values()]))

                trk_tot = z3.Bool(f"track_tot_{tot.id}")
                track_cross[str(trk_tot)] = tot.id
                s_cross.assert_and_track(total_var <= tot.upper, trk_tot)

                sec_ins_used = []
                for sec in section_scopes:
                    sec_ins = [ins for ins in instructions if ins.kind == 'numerical' and ins.key == 'word' and ins.scope == sec and ins.lower is not None]
                    if sec_ins:
                        best_ins = max(sec_ins, key=lambda x: x.lower or 0)
                        sec_ins_used.append(best_ins)
                        trk_sec = z3.Bool(f"track_sec_{best_ins.id}")
                        track_cross[str(trk_sec)] = best_ins.id
                        s_cross.assert_and_track(sec_vars[sec] >= best_ins.lower, trk_sec)

                if len(sec_ins_used) >= 2 and s_cross.check() == z3.unsat:
                    core = s_cross.unsat_core()
                    conflicting_ids = list(dict.fromkeys(track_cross[str(t)] for t in core if str(t) in track_cross))
                    if len(conflicting_ids) >= 2:
                        sum_min = sum((i.lower or 0) for i in sec_ins_used if i.id in conflicting_ids)
                        conflicts.append(Conflict(
                            instruction_ids=conflicting_ids,
                            kind='numerical',
                            explanation=f"Cross-scope contradiction: total word limit ({tot.upper}) is less than the sum of mandatory section minimum requirements ({sum_min}).",
                            severity='hard',
                            source='rule'
                        ))

        return conflicts
