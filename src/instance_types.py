import random
class AccountingRequest:
    """A structured representation of a parsed access control request."""

    def __init__(
        self,
        roles,
        is_in_training,
        action_type,
        resource_type,
        is_under_audit,
        is_archived,
        person_no=None,
    ):
        self.person_no = person_no or random.choice(list(range(0, 5)))
        self.roles = roles or {}
        self.is_in_training = is_in_training
        self.action_type = action_type
        self.resource_type = resource_type
        self.is_under_audit = is_under_audit
        self.is_archived = is_archived

    def print_readable(self):
        """Prints the request details in a user-friendly format."""
        print(f"Subject: Person{self.person_no}")
        roles_str = ", ".join(self.roles) if self.roles else "None"
        print(f"  - Roles: [{roles_str}]")
        print(f"  - In Training: {'Yes' if self.is_in_training else 'No'}")

        print(f"Action: {self.action_type}")

        print(f"Resource: {self.resource_type}")
        print(f"  - Under Audit: {'Yes' if self.is_under_audit else 'No'}")
        print(f"  - Archived: {'Yes' if self.is_archived else 'No'}")

    def __str__(self):
        result = f"Subject: Person{self.person_no}\n"

        roles_str = ", ".join(sorted(self.roles))  # sort for consistent order
        result += f"  Roles: {{{roles_str}}}\n"
        result += f"  In Training: {self.is_in_training}\n"

        result += f"Action: {self.action_type}\n"
        result += f"Resource: {self.resource_type}\n"
        result += f"  Under Audit: {self.is_under_audit}\n"
        result += f"  Archived: {self.is_archived}"

        return result

    def __eq__(self, other):
        if not isinstance(other, AccountingRequest):
            return False
        return (
            self.roles == other.roles and
            self.is_in_training == other.is_in_training and
            self.action_type == other.action_type and
            self.resource_type == other.resource_type and
            self.is_under_audit == other.is_under_audit and
            self.is_archived == other.is_archived
        )

    def __hash__(self):
        return hash((
            tuple(self.roles),
            self.is_in_training,
            self.action_type,
            self.resource_type,
            self.is_under_audit,
            self.is_archived
        ))


class TechRequest:
    """A structured representation of a parsed access control request."""

    def __init__(
        self,
        roles,
        is_on_call,
        action_type,
        resource_type,
        is_privileged,
        is_after_hours,
        person_no=None

    ):
        self.person_no = person_no or random.choice(list(range(0, 5)))
        self.roles = roles or {}
        self.is_on_call = is_on_call
        self.action_type = action_type
        self.resource_type = resource_type
        self.is_privileged = is_privileged
        self.is_after_hours = is_after_hours

    def print_readable(self):
        """Prints the request details in a user-friendly format."""
        print(f"Subject: Person{self.person_no}")
        roles_str = ", ".join(self.roles) if self.roles else "None"
        print(f"  - Roles: [{roles_str}]")
        print(f"  - On Call: {'Yes' if self.is_on_call else 'No'}")

        print(f"Action: {self.action_type}")
        print(f"  - Privileged: {'Yes' if self.is_privileged else 'No'}")

        print(f"Resource: {self.resource_type}")
        print(f"  - After Hours: {'Yes' if self.is_after_hours else 'No'}")

    def __str__(self):
        result = f"Subject: Person{self.person_no}\n"

        roles_str = ", ".join(sorted(self.roles))  # sort for consistent order
        result += f"  Roles: {{{roles_str}}}\n"
        result += f"  On Call: {self.is_on_call}\n"

        result += f"Action: {self.action_type}\n"
        result += f"  Privileged: {self.is_privileged}\n"

        result += f"Resource: {self.resource_type}\n"
        result += f"  After Hours: {self.is_after_hours}"

        return result

    def __eq__(self, other):
        if not isinstance(other, TechRequest):
            return False
        return (
            self.roles == other.roles
            and self.is_on_call == other.is_on_call
            and self.action_type == other.action_type
            and self.is_privileged == other.is_privileged
            and self.resource_type == other.resource_type
            and self.is_after_hours == other.is_after_hours
        )

    def __hash__(self):
        return hash(
            (
                tuple(self.roles),
                self.is_on_call,
                self.action_type,
                self.resource_type,
                self.is_privileged,
                self.is_after_hours,
            )
        )


class GradingRequest:
    """A structured representation of a parsed access control request."""

    def __init__(
        self,
        roles,
        action_type,
        resource_type,
        is_submitted,
        person_no=None,
    ):
        self.person_no = person_no or random.choice(list(range(0, 5)))
        self.roles = roles or {}
        self.action_type = action_type
        self.resource_type = resource_type
        self.is_submitted = is_submitted

    def print_readable(self):
        """Prints the request details in a user-friendly format."""
        print(f"Subject: Person{self.person_no}")
        roles_str = ", ".join(self.roles) if self.roles else "None"
        print(f"  - Roles: [{roles_str}]")

        print(f"Action: {self.action_type}")

        print(f"Resource: {self.resource_type}")
        print(f"  - Submitted: {'Yes' if self.is_submitted else 'No'}")

    def __str__(self):
        result = f"Subject: Person{self.person_no}\n"

        roles_str = ", ".join(sorted(self.roles))  # sort for consistent order
        result += f"  Roles: {{{roles_str}}}\n"


        result += f"Action: {self.action_type}\n"
        result += f"Resource: {self.resource_type}\n"
        result += f"  Submitted: {self.is_submitted}\n"

        return result

    def __eq__(self, other):
        if not isinstance(other, GradingRequest):
            return False
        return (
            self.roles == other.roles
            and self.action_type == other.action_type
            and self.resource_type == other.resource_type
            and self.is_submitted == other.is_submitted
        )

    def __hash__(self):
        return hash(
            (
                tuple(self.roles),
                self.action_type,
                self.resource_type,
                self.is_submitted,
            )
        )
