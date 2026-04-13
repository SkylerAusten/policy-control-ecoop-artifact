#!/usr/bin/env python3
"""
Parses a Forge output file containing multiple satisfying instances for the
Company Audit model, and prints each parsed request in a readable format.
"""
import re
import sys
from pathlib import Path
from instance_types import AccountingRequest, GradingRequest, TechRequest

def accounting_parser(instance_str: str) -> AccountingRequest:
    """
    Parses a Forge instance string from the complex Company Audit model
    to create an AccountingRequest object.
    """

    # Helper to get the full content of a relation (e.g., all pairs in the relation)
    def get_relation_content(relation_name, text):
        # Updated pattern to match the actual Forge output format
        # Looking for patterns like (relation_name . ((content)))
        pattern = re.compile(rf"\({relation_name} \. \(\((.*?)\)\)\)")
        match = pattern.search(text)
        if match:
            return match.group(1)

        # Try alternative pattern for empty relations
        empty_pattern = re.compile(rf"\({relation_name} \. \(\)\)")
        if empty_pattern.search(text):
            return ""

        return ""

    # 1. Map all concrete atoms to their signature types
    atom_to_type = {}
    type_names = (
        "Read",
        "Edit",
        "FinancialReport",
        "LegalDocument",
        "Admin",
        "Accountant",
    )
    type_pattern = re.compile(r"\((" + "|".join(type_names) + r") \. \(\((.*?)\)\)\)")
    for match in type_pattern.finditer(instance_str):
        type_name, atoms_str = match.groups()
        for atom in atoms_str.strip().split(" "):
            if atom:
                atom_to_type[atom] = type_name

    # 2. Find the atoms for the request's subject, action, and resource
    req_content = get_relation_content("Request", instance_str)
    if not req_content:
        raise ValueError("Request singleton not found.")
    req_atom = req_content.split(" ")[0]

    # Look for reqSubject, reqAction, reqResource relations containing the request atom
    subject_pattern = re.compile(rf"reqSubject \. \(\(({req_atom} \w+)\)\)")
    action_pattern = re.compile(rf"reqAction \. \(\(({req_atom} \w+)\)\)")
    resource_pattern = re.compile(rf"reqResource \. \(\(({req_atom} \w+)\)\)")

    subject_match = subject_pattern.search(instance_str)
    action_match = action_pattern.search(instance_str)
    resource_match = resource_pattern.search(instance_str)

    if not (subject_match and action_match and resource_match):
        raise ValueError("Instance string does not contain a complete request.")

    subject_atom = subject_match.group(1).split()[1]  # Get the second atom (subject)
    action_atom = action_match.group(1).split()[1]    # Get the second atom (action)
    resource_atom = resource_match.group(1).split()[1] # Get the second atom (resource)

    if not all((subject_atom, action_atom, resource_atom)):
        raise ValueError("Instance string does not contain a complete request.")

    # 3. Determine Subject Details
    roles = []
    is_in_training = False
    # Check training status
    training_content = get_relation_content("inTraining", instance_str)
    if f"{subject_atom} True0" in training_content:
        is_in_training = True

    # Find roles - look for pairs like (Subject3 AccountantRole0) in the roles relation
    roles_content = get_relation_content("roles", instance_str)
    if roles_content:
        # Use regex to find all role pairs involving our subject
        # Pattern matches: Subject3 RoleAtom (with optional closing parentheses)
        role_pattern = re.compile(rf"{re.escape(subject_atom)}\s+(\w+)\)?")
        role_matches = role_pattern.findall(roles_content)

        for role_atom in role_matches:
            role_atom = role_atom.rstrip(')')  # Remove any trailing parenthesis
            role_type = atom_to_type.get(role_atom, "UnknownRole")
            if role_type != "UnknownRole":
                role_name = role_type.replace("Role", "")  # e.g., AdminRole -> Admin
                if role_name not in roles:  # Avoid duplicates
                    roles.append(role_name)

    # 4. Determine Action and Resource Types
    action_type = atom_to_type.get(action_atom)
    resource_type = atom_to_type.get(resource_atom)

    # 5. Determine boolean attributes of the Resource
    audit_content = get_relation_content("underAudit", instance_str)
    archived_content = get_relation_content("archived", instance_str)

    is_under_audit = f"{resource_atom} True0" in audit_content
    is_archived = f"{resource_atom} True0" in archived_content

    # 6. Create and return the final object
    return AccountingRequest(
        roles=set(roles),
        is_in_training=is_in_training,
        action_type=action_type,
        resource_type=resource_type,
        is_under_audit=is_under_audit,
        is_archived=is_archived,
    )


def grading_parser(instance_str: str) -> GradingRequest:
    """
    Parses a Forge instance string from the complex Company Audit model
    to create an GradingRequest object.
    """

    # Helper to get the full content of a relation (e.g., all pairs in the relation)
    def get_relation_content(relation_name, text):
        # Updated pattern to match the actual Forge output format
        # Looking for patterns like (relation_name . ((content)))
        pattern = re.compile(rf"\({relation_name} \. \(\((.*?)\)\)\)")
        match = pattern.search(text)
        if match:
            return match.group(1)

        # Try alternative pattern for empty relations
        empty_pattern = re.compile(rf"\({relation_name} \. \(\)\)")
        if empty_pattern.search(text):
            return ""

        return ""

    # 1. Map all concrete atoms to their signature types
    atom_to_type = {}
    type_names = (
        "View",
        "Grade",
        "Assignment",
        "Exam",
        "Student",
        "Professor",
        "TeachingAssistant"
    )
    type_pattern = re.compile(r"\((" + "|".join(type_names) + r") \. \(\((.*?)\)\)\)")
    for match in type_pattern.finditer(instance_str):
        type_name, atoms_str = match.groups()
        for atom in atoms_str.strip().split(" "):
            if atom:
                atom_to_type[atom] = type_name

    # 2. Find the atoms for the request's subject, action, and resource
    req_content = get_relation_content("Request", instance_str)
    if not req_content:
        raise ValueError("Request singleton not found.")
    req_atom = req_content.split(" ")[0]

    # Look for reqSubject, reqAction, reqResource relations containing the request atom
    subject_pattern = re.compile(rf"reqSubject \. \(\(({req_atom} \w+)\)\)")
    action_pattern = re.compile(rf"reqAction \. \(\(({req_atom} \w+)\)\)")
    resource_pattern = re.compile(rf"reqResource \. \(\(({req_atom} \w+)\)\)")

    subject_match = subject_pattern.search(instance_str)
    action_match = action_pattern.search(instance_str)
    resource_match = resource_pattern.search(instance_str)

    if not (subject_match and action_match and resource_match):
        raise ValueError("Instance string does not contain a complete request.")

    subject_atom = subject_match.group(1).split()[1]  # Get the second atom (subject)
    action_atom = action_match.group(1).split()[1]  # Get the second atom (action)
    resource_atom = resource_match.group(1).split()[1]  # Get the second atom (resource)

    if not all((subject_atom, action_atom, resource_atom)):
        raise ValueError("Instance string does not contain a complete request.")

    # 3. Determine Subject Details
    roles = []

    # Find roles - look for pairs like (Subject3 AccountantRole0) in the roles relation
    roles_content = get_relation_content("roles", instance_str)
    if roles_content:
        # Use regex to find all role pairs involving our subject
        # Pattern matches: Subject3 RoleAtom (with optional closing parentheses)
        role_pattern = re.compile(rf"{re.escape(subject_atom)}\s+(\w+)\)?")
        role_matches = role_pattern.findall(roles_content)

        for role_atom in role_matches:
            role_atom = role_atom.rstrip(")")  # Remove any trailing parenthesis
            role_type = atom_to_type.get(role_atom, "UnknownRole")
            if role_type != "UnknownRole":
                role_name = role_type.replace("Role", "")  # e.g., AdminRole -> Admin
                if role_name not in roles:  # Avoid duplicates
                    roles.append(role_name)

    # 4. Determine Action and Resource Types
    action_type = atom_to_type.get(action_atom)
    resource_type = atom_to_type.get(resource_atom)

    # 5. Determine boolean attributes of the Resource
    submitted_content = get_relation_content("submitted", instance_str)

    is_submitted = f"{resource_atom} True0" in submitted_content

    # 6. Create and return the final object
    return GradingRequest(
        roles=set(roles),
        action_type=action_type,
        resource_type=resource_type,
        is_submitted=is_submitted,
    )


def tech_parser(instance_str: str) -> TechRequest:
    """
    Parses a Forge instance string from the complex Company Audit model
    to create an TechRequest object.
    """

    # Helper to get the full content of a relation (e.g., all pairs in the relation)
    def get_relation_content(relation_name, text):
        # Updated pattern to match the actual Forge output format
        # Looking for patterns like (relation_name . ((content)))
        pattern = re.compile(rf"\({relation_name} \. \(\((.*?)\)\)\)")
        match = pattern.search(text)
        if match:
            return match.group(1)

        # Try alternative pattern for empty relations
        empty_pattern = re.compile(rf"\({relation_name} \. \(\)\)")
        if empty_pattern.search(text):
            return ""

        return ""

    # 1. Map all concrete atoms to their signature types
    atom_to_type = {}
    type_names = (
        "Access",
        "Edit",
        "Server",
        "Firewall",
        "SystemAdmin",
        "NetworkAdmin",
    )
    type_pattern = re.compile(r"\((" + "|".join(type_names) + r") \. \(\((.*?)\)\)\)")
    for match in type_pattern.finditer(instance_str):
        type_name, atoms_str = match.groups()
        for atom in atoms_str.strip().split(" "):
            if atom:
                atom_to_type[atom] = type_name

    # 2. Find the atoms for the request's subject, action, and resource
    req_content = get_relation_content("Request", instance_str)
    if not req_content:
        raise ValueError("Request singleton not found.")
    req_atom = req_content.split(" ")[0]

    # Look for reqSubject, reqAction, reqResource relations containing the request atom
    subject_pattern = re.compile(rf"reqSubject \. \(\(({req_atom} \w+)\)\)")
    action_pattern = re.compile(rf"reqAction \. \(\(({req_atom} \w+)\)\)")
    resource_pattern = re.compile(rf"reqResource \. \(\(({req_atom} \w+)\)\)")

    subject_match = subject_pattern.search(instance_str)
    action_match = action_pattern.search(instance_str)
    resource_match = resource_pattern.search(instance_str)

    if not (subject_match and action_match and resource_match):
        raise ValueError("Instance string does not contain a complete request.")

    subject_atom = subject_match.group(1).split()[1]  # Get the second atom (subject)
    action_atom = action_match.group(1).split()[1]  # Get the second atom (action)
    resource_atom = resource_match.group(1).split()[1]  # Get the second atom (resource)

    if not all((subject_atom, action_atom, resource_atom)):
        raise ValueError("Instance string does not contain a complete request.")

    # 3. Determine Subject Details
    roles = []
    is_on_call = False
    # Check on-call status
    oncall_content = get_relation_content("isOnCall", instance_str)
    if f"{subject_atom} True0" in oncall_content:
        is_on_call = True

    # Find roles - look for pairs like (Subject3 AccountantRole0) in the roles relation
    roles_content = get_relation_content("roles", instance_str)
    if roles_content:
        # Use regex to find all role pairs involving our subject
        # Pattern matches: Subject3 RoleAtom (with optional closing parentheses)
        role_pattern = re.compile(rf"{re.escape(subject_atom)}\s+(\w+)\)?")
        role_matches = role_pattern.findall(roles_content)

        for role_atom in role_matches:
            role_atom = role_atom.rstrip(")")  # Remove any trailing parenthesis
            role_type = atom_to_type.get(role_atom, "UnknownRole")
            if role_type != "UnknownRole":
                role_name = role_type.replace("Role", "")  # e.g., AdminRole -> Admin
                if role_name not in roles:  # Avoid duplicates
                    roles.append(role_name)

    # 4. Determine Action and Resource Types
    action_type = atom_to_type.get(action_atom)
    resource_type = atom_to_type.get(resource_atom)

    # 5. Determine boolean attributes of the Action & Resource
    privileged_content = get_relation_content("isPrivileged", instance_str)
    afterhours_content = get_relation_content("isAfterHours", instance_str)

    is_privileged = f"{action_atom} True0" in privileged_content
    is_after_hours = f"{resource_atom} True0" in afterhours_content

    # 6. Create and return the final object
    return TechRequest(
        roles=set(roles),
        is_on_call=is_on_call,
        is_privileged=is_privileged,
        action_type=action_type,
        resource_type=resource_type,
        is_after_hours=is_after_hours,
    )


def main():
    """Main function to read a file and parse its instances."""
    if len(sys.argv) < 2:
        print("Usage: python parse_results.py <path_to_output_file>")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"Error: File not found at '{input_file}'")
        sys.exit(1)

    print(f"📄 Parsing instances from: {input_file.name}\n")

    try:
        content = input_file.read_text(encoding="utf-8")

        # Find all instance strings in the file
        # Updated pattern to match the actual Forge output format
        instance_strings = re.findall(
            r"(#\(struct:Sat .*?\)\)\) \(\(.*?\)\) \(\)\))", content, re.DOTALL
        )

        if not instance_strings:
            print("No satisfying instances found in the file.")
            return

        for i, instance_str in enumerate(instance_strings):
            print(f"--- Instance {i + 1} ---")
            try:
                parsed_request = accounting_parser(instance_str)
                parsed_request.print_readable()
                print("-" * 18 + "\n")
            except (ValueError, AttributeError) as e:
                print(f"❌ Failed to parse this instance: {e}")
                print("-" * 18 + "\n")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
