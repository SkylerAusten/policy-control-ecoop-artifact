import os
import re
from pathlib import Path
from typing import Set, Dict, List, Tuple, Optional
import random
from instance_types import AccountingRequest
from hashset_parsers import accounting_parser

accounting_relationships = {
    ("correct", "alt1"): "superset",
    ("alt1", "correct"): "subset",
    ("correct", "alt2"): "subset",
    ("alt2", "correct"): "superset",
    ("correct", "alt3"): "overlap",
    ("alt3", "correct"): "overlap",
    ("alt1", "alt2"): "subset",
    ("alt2", "alt1"): "superset",
    ("alt1", "alt3"): "overlap",
    ("alt3", "alt1"): "overlap",
    ("alt2", "alt3"): "overlap",
    ("alt3", "alt2"): "overlap",
}

class AccountingInstanceDatabase:
    """A database to store and manage unique AccountingRequest instances."""

    def __init__(self):
        # Store all unique instances
        self.instances: Set[AccountingRequest] = set()
        # Map policy combinations to their instances
        self.policy_instances: Dict[str, Set[AccountingRequest]] = {}
        # Map individual policies to their instances
        self.individual_policies: Dict[str, Set[AccountingRequest]] = {
            "correct": set(),
            "alt1": set(),
            "alt2": set(),
            "alt3": set()
        }

    def load_from_files(self, output_dir: str = "accounting_combo_outputs"):
        """Load instances from all .txt files in the output directory."""
        output_path = Path(output_dir)
        if not output_path.exists():
            raise FileNotFoundError(f"Output directory {output_dir} not found")

        for file_path in output_path.glob("combo_*.txt"):
            policy_combo = file_path.stem  # Get filename without extension
            instances = self._parse_file(file_path)
            self.policy_instances[policy_combo] = instances
            self.instances.update(instances)

            # Parse which individual policies are active in this combination
            self._update_individual_policies(policy_combo, instances)
            print(f"Loaded {len(instances)} instances from {policy_combo}")

    def _update_individual_policies(self, policy_combo: str, instances: Set[AccountingRequest]):
        """Update individual policy mappings based on the combo name."""
        # Parse the combo name to determine which policies are active
        # Example: "combo_correct_alt1_not_alt2_alt3" means correct=True, alt1=True, alt2=False, alt3=True
        # We only add instances to a policy if that policy is TRUE in the combo
        parts = policy_combo.split("_")

        active_policies = set()
        for i, part in enumerate(parts):
            if part in ["correct", "alt1", "alt2", "alt3"]:
                # Check if this policy is active (not preceded by "not")
                if i == 0 or parts[i-1] != "not":
                    active_policies.add(part)

        # Add instances to each active policy
        for policy in active_policies:
            self.individual_policies[policy].update(instances)

    def _parse_file(self, file_path: Path) -> Set[AccountingRequest]:
        """Parse instances from a single output file."""
        instances = set()
        try:
            content = file_path.read_text(encoding="utf-8")
            # Find all instance strings in the file
            instance_strings = re.findall(
                r"(#\(struct:Sat .*?\)\)\) \(\(.*?\)\) \(\)\))", content, re.DOTALL
            )

            for instance_str in instance_strings:
                try:
                    parsed_request = accounting_parser(instance_str)
                    instances.add(parsed_request)
                except (ValueError, AttributeError) as e:
                    print(f"Warning: Failed to parse instance in {file_path.name}: {e}")

        except Exception as e:
            print(f"Error reading file {file_path}: {e}")

        return instances

    def is_instance_in_policy(self, instance: AccountingRequest, policy: str) -> bool:
        """
        Checks if the instance exists in the given policy.
        Policy can be either individual policy (correct, alt1, alt2, alt3) or full combo name.
        """

        print("Instance:", instance)
        print(
            "Instance in policy?", instance in self.policy_instances[policy]
        )

        if policy in self.individual_policies:
            return instance in self.individual_policies[policy]
        elif policy in self.policy_instances:
            return instance in self.policy_instances[policy]
        else:
            raise ValueError(f"Unknown policy: {policy}")

    def get_instances_in_policy(self, policy: str) -> Set[AccountingRequest]:
        """Get all instances for a given policy (individual policy or combo name)."""
        if policy in self.individual_policies:
            return self.individual_policies[policy]
        elif policy in self.policy_instances:
            return self.policy_instances[policy]
        else:
            return set()

    def get_instances_in_policy_combo(self, policy_combo: str) -> Set[AccountingRequest]:
        """Get all instances for a given policy combination."""
        return self.policy_instances.get(policy_combo, set())

    def get_instances_in_both_policies(self, policy1: str, policy2: str) -> Set[AccountingRequest]:
        """Get instances that exist in both policy combinations."""
        set1 = self.get_instances_in_policy(policy1)
        set2 = self.get_instances_in_policy(policy2)
        return set1.intersection(set2)

    def get_instances_in_first_not_second(self, policy1: str, policy2: str) -> Set[AccountingRequest]:
        """Get instances that exist in policy1 but not in policy2."""
        set1 = self.get_instances_in_policy(policy1)
        set2 = self.get_instances_in_policy(policy2)
        return set1.difference(set2)

    def get_distinguishing_instances(self, policy1: str, policy2: str) -> Tuple[Set[AccountingRequest], Set[AccountingRequest]]:
        """
        Get instances that distinguish between two policies.
        Returns (instances_only_in_policy1, instances_only_in_policy2)
        """
        only_in_1 = self.get_instances_in_first_not_second(policy1, policy2)
        only_in_2 = self.get_instances_in_first_not_second(policy2, policy1)
        return only_in_1, only_in_2

    def get_individual_policies(self) -> List[str]:
        """Get list of individual policy names."""
        return list(self.individual_policies.keys())

    def query_individual_policy_differences(self, policy1: str, policy2: str):
        """Print a detailed comparison of two individual policies."""
        if policy1 not in self.individual_policies:
            raise ValueError(f"Unknown individual policy: {policy1}")
        if policy2 not in self.individual_policies:
            raise ValueError(f"Unknown individual policy: {policy2}")

        print(f"\n=== Individual Policy Comparison: {policy1} vs {policy2} ===")

        set1 = self.individual_policies[policy1]
        set2 = self.individual_policies[policy2]
        common = set1.intersection(set2)
        only_1 = set1 - set2
        only_2 = set2 - set1

        print(f"Total instances in {policy1}: {len(set1)}")
        print(f"Total instances in {policy2}: {len(set2)}")
        print(f"Common instances: {len(common)}")
        print(f"Only in {policy1}: {len(only_1)}")
        print(f"Only in {policy2}: {len(only_2)}")

        if only_1:
            print(f"\nSample instances only allowed by {policy1}:")
            for i, instance in enumerate(list(only_1)[:3]):  # Show first 3
                print(f"  {i+1}. {instance}")

        if only_2:
            print(f"\nSample instances only allowed by {policy2}:")
            for i, instance in enumerate(list(only_2)[:3]):  # Show first 3
                print(f"  {i+1}. {instance}")

    def is_instance_allowed_by_individual_policy(self, instance: AccountingRequest, policy: str) -> bool:
        """Check if an instance is allowed by a specific individual policy."""
        if policy not in self.individual_policies:
            raise ValueError(f"Unknown individual policy: {policy}")
        return instance in self.individual_policies[policy]

    def gen_diff_instance(self, in_policy: str, not_policy: str, seen_instances: Set[AccountingRequest]) -> Optional[AccountingRequest]:
        """Loop through instances that are in the in_policy but not in the not_policy until a new one (not in seen_instances) is found."""
        candidates = self.get_instances_in_first_not_second(in_policy, not_policy)
        unseen_candidates = candidates - seen_instances

        if unseen_candidates:
            return random.choice(list(unseen_candidates))
        return None

    def gen_instance_in_both(self, policy1: str, policy2: str, seen_instances: Set[AccountingRequest]) -> Optional[AccountingRequest]:
        """Loop through instances that are in both policies until a new one (not in seen_instances) is found."""
        candidates = self.get_instances_in_both_policies(policy1, policy2)
        unseen_candidates = candidates - seen_instances

        if unseen_candidates:
            return random.choice(list(unseen_candidates))
        return None

    def generate_instances(self, policies_in_play: List[str], eliminated_policies: List[str], seen_instances: Set[AccountingRequest]) -> Tuple[Optional[AccountingRequest], Optional[AccountingRequest]]:
        """
        Generate two new instances based on the policies in play and eliminated policies.
        Uses seen_instances to avoid duplicates.
        """

        p0, p1 = None, None

        if len(policies_in_play) == 0:
            raise ValueError("At least one policy must be in play.")

        elif len(policies_in_play) == 1:
            p0 = policies_in_play[0]

            # TODO: Pick a random policy, not the first one.
            p1 = eliminated_policies[0]

        else:
            p0 = policies_in_play[0]
            p1 = policies_in_play[1]

        rel = accounting_relationships.get((p0, p1), None)

        if rel is None:
            raise ValueError(f"No known relationship between policies {p0} and {p1}.")

        if rel == "overlap":
            return self.gen_diff_instance(p0, p1, seen_instances), self.gen_diff_instance(p1, p0, seen_instances)
        elif rel == "disjoint":
            return self.gen_diff_instance(p0, p1, seen_instances), self.gen_diff_instance(p1, p0, seen_instances)
        elif rel == "subset":
            return self.gen_instance_in_both(p0, p1, seen_instances), self.gen_diff_instance(p1, p0, seen_instances)
        elif rel == "superset":
            return self.gen_diff_instance(p0, p1, seen_instances), self.gen_instance_in_both(p1, p0, seen_instances)
        else:
            raise ValueError(f"Unhandled relationship type: {rel}")

    def find_instances_by_criteria(self, **criteria) -> Set[AccountingRequest]:
        """
        Find instances matching specific criteria.
        Example: find_instances_by_criteria(subject_type="Employee", action_type="Edit", is_in_training=True)
        """
        matching = set()
        for instance in self.instances:
            match = True
            for key, value in criteria.items():
                if not hasattr(instance, key):
                    match = False
                    break
                instance_value = getattr(instance, key)
                if key == "roles":  # Special handling for roles (list)
                    if isinstance(value, str):
                        match = value in instance_value
                    elif isinstance(value, list):
                        match = all(role in instance_value for role in value)
                    else:
                        match = False
                else:
                    match = instance_value == value
                if not match:
                    break
            if match:
                matching.add(instance)
        return matching

    def get_policy_combo_name(self, correct: bool, alt1: bool, alt2: bool, alt3: bool) -> str:
        """Generate policy combo name from boolean values."""
        parts = ["combo"]
        parts.append("correct" if correct else "not_correct")
        parts.append("alt1" if alt1 else "not_alt1")
        parts.append("alt2" if alt2 else "not_alt2")
        parts.append("alt3" if alt3 else "not_alt3")
        return "_".join(parts)

    def query_by_policy_bools(self, correct: bool, alt1: bool, alt2: bool, alt3: bool) -> Set[AccountingRequest]:
        """Query instances using boolean policy values."""
        policy_name = self.get_policy_combo_name(correct, alt1, alt2, alt3)
        return self.get_instances_in_policy(policy_name)

    def is_instance_allowed_by_policy(self, instance: AccountingRequest, correct: bool, alt1: bool, alt2: bool, alt3: bool) -> bool:
        """Check if an instance is allowed by a specific policy combination."""
        policy_name = self.get_policy_combo_name(correct, alt1, alt2, alt3)
        return self.is_instance_in_policy(instance, policy_name)

    def get_available_policies(self) -> List[str]:
        """Get list of all available policy combinations."""
        return list(self.policy_instances.keys())


def build_database(output_dir: str = "accounting_combo_outputs") -> AccountingInstanceDatabase:
    """Build and return the accounting instance database."""
    db = AccountingInstanceDatabase()
    db.load_from_files(output_dir)
    return db


def main():
    """Example usage of the database."""
    try:
        # Build the database
        print("Building accounting instance database...")
        db = build_database()

        seen_instances = set()
        count = 0

        while True:
            word1, word2 = db.generate_instances(["correct", "alt2"], ["alt1", "alt3"], seen_instances)
            if word1 is None or word2 is None:
                break

            if word1 is not None:
                count += 1
                seen_instances.add(word1)

            if word2 is not None:
                count += 1
                seen_instances.add(word2)

            if (db.is_instance_in_policy(word1, "alt2") and 
                not db.is_instance_in_policy(word2, "correct") and
                db.is_instance_in_policy(word1, "correct") and
                db.is_instance_in_policy(word2, "alt2")):
                print("Expected behavior!")
            else:
                print("Unexpected behavior!", 
                      word1, 
                      db.is_instance_in_policy(word1, "correct"), 
                      db.is_instance_in_policy(word1, "alt2"),
                      word2, 
                      db.is_instance_in_policy(word2, "correct"),
                      db.is_instance_in_policy(word2, "alt2"))

        print(f"Generated {count} unique instances from the database.")


        return db
        
    except Exception as e:
        print(f"Error building database: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()
