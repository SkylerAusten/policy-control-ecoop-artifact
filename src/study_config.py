accounting_description = """
<b>Admins can...</b>
  - read all resources.
  - edit all resources, unless the admin is in training or the resource is under audit.
<b>Accountants can...</b>
  - read all resources, unless the resource is archived.
  - edit financial reports (not legal documents), unless the report is archived or under audit or the accountant is in training.

<b>All other requests are denied.</b>
""".strip()

accounting_correct = """
<pre class="policy-code" style="font-family: 'Courier New', Courier, monospace; line-height: 1.2; white-space: pre-wrap; word-break: break-word;">
permits = {
  (<span class="request-subject">role</span> = Admin and <span class="request-action">act</span> = Read) or
  (<span class="request-subject">role</span> = Admin and <span class="request-action">act</span> = Edit) or
  (<span class="request-subject">role</span> = Accountant and <span class="request-action">act</span> = Read) or
  (<span class="request-subject">role</span> = Accountant and <span class="request-action">act</span> = Edit and <span class="request-resource">res</span> = FinancialReport)
}

denies = {
  (<span class="request-subject">role</span> = Admin and <span class="request-action">act</span> = Edit and 
    (<span class="request-subject">sub</span>.inTraining = True or <span class="request-resource">res</span>.underAudit = True)) or
  (<span class="request-subject">role</span> = Accountant and <span class="request-action">act</span> = Read and <span class="request-resource">res</span>.archived = True) or
  (<span class="request-subject">role</span> = Accountant and <span class="request-action">act</span> = Edit and <span class="request-resource">res</span> = LegalDocument) or
  (<span class="request-subject">role</span> = Accountant and <span class="request-action">act</span> = Edit and <span class="request-resource">res</span> = FinancialReport and 
    (<span class="request-resource">res</span>.archived = True or <span class="request-resource">res</span>.underAudit = True or <span class="request-subject">sub</span>.inTraining = True))
}
</pre>
""".strip()

accounting_alt1 = """
<pre class="policy-code" style="font-family: 'Courier New', Courier, monospace; line-height: 1.2; white-space: pre-wrap; word-break: break-word;">
permits = {
  (<span class="request-subject">role</span> = Admin and <span class="request-action">act</span> = Read) or
  (<span class="request-subject">role</span> = Admin and <span class="request-action">act</span> = Edit) or
  (<span class="request-subject">role</span> = Accountant and <span class="request-action">act</span> = Read) or
  (<span class="request-subject">role</span> = Accountant and <span class="request-action">act</span> = Edit and <span class="request-resource">res</span> = FinancialReport)
}

denies = {
  (<span class="request-subject">sub</span>.inTraining = True) or
  (<span class="request-subject">role</span> = Admin and <span class="request-action">act</span> = Edit and 
    (<span class="request-subject">sub</span>.inTraining = True or <span class="request-resource">res</span>.underAudit = True)) or
  (<span class="request-subject">role</span> = Accountant and <span class="request-action">act</span> = Read and <span class="request-resource">res</span>.archived = True) or
  (<span class="request-subject">role</span> = Accountant and <span class="request-action">act</span> = Edit and <span class="request-resource">res</span> = LegalDocument) or
  (<span class="request-subject">role</span> = Accountant and <span class="request-action">act</span> = Edit and <span class="request-resource">res</span> = FinancialReport and 
    (<span class="request-resource">res</span>.archived = True or <span class="request-resource">res</span>.underAudit = True or <span class="request-subject">sub</span>.inTraining = True))
}
</pre>
""".strip()

accounting_alt2 = """
<pre class="policy-code" style="font-family: 'Courier New', Courier, monospace; line-height: 1.2; white-space: pre-wrap; word-break: break-word;">
permits = {
  (<span class="request-subject">role</span> = Admin and <span class="request-action">act</span> = Read) or
  (<span class="request-subject">role</span> = Admin and <span class="request-action">act</span> = Edit) or
  (<span class="request-subject">role</span> = Accountant and <span class="request-action">act</span> = Read) or
  (<span class="request-subject">role</span> = Accountant and <span class="request-action">act</span> = Edit and <span class="request-resource">res</span> = FinancialReport)
}

denies = {
  (<span class="request-subject">role</span> = Accountant and <span class="request-action">act</span> = Read and <span class="request-resource">res</span>.archived = True) or
  (<span class="request-subject">role</span> = Accountant and <span class="request-action">act</span> = Edit and <span class="request-resource">res</span> = LegalDocument) or
  (<span class="request-subject">role</span> = Accountant and <span class="request-action">act</span> = Edit and <span class="request-resource">res</span> = FinancialReport and 
    (<span class="request-resource">res</span>.archived = True or <span class="request-resource">res</span>.underAudit = True or <span class="request-subject">sub</span>.inTraining = True))
}
</pre>
""".strip()

accounting_alt3 = """
<pre class="policy-code" style="font-family: 'Courier New', Courier, monospace; line-height: 1.2; white-space: pre-wrap; word-break: break-word;">
permits = {
  (<span class="request-subject">role</span> = Admin and <span class="request-action">act</span> = Read) or
  (<span class="request-subject">role</span> = Admin and <span class="request-action">act</span> = Edit) or
  (<span class="request-subject">role</span> = Accountant and <span class="request-action">act</span> = Read) or
  (<span class="request-subject">role</span> = Accountant and <span class="request-action">act</span> = Edit and <span class="request-resource">res</span> = FinancialReport)
}

denies = {
  (<span class="request-subject">role</span> = Admin and <span class="request-action">act</span> = Edit and 
    (<span class="request-subject">sub</span>.inTraining = True or <span class="request-resource">res</span>.underAudit = True or <span class="request-resource">res</span> = LegalDocument)) or
  (<span class="request-subject">role</span> = Accountant and <span class="request-action">act</span> = Read and <span class="request-resource">res</span>.archived = True) or
  (<span class="request-subject">role</span> = Accountant and <span class="request-action">act</span> = Edit and <span class="request-resource">res</span> = LegalDocument) or
  (<span class="request-subject">role</span> = Accountant and <span class="request-action">act</span> = Edit and <span class="request-resource">res</span> = FinancialReport and <span class="request-subject">sub</span>.inTraining = True)
}
</pre>
""".strip()


grading_description = """
<b>Professors can...</b>
  - view and grade any submitted resource (assignment or exam).
<b>Teaching Assistants can...</b>
  - view and grade any submitted assignment.
<b>Students can...</b>
  - view any submitted assignment.
  - view any unsubmitted resource (assignment or exam).

<b>All other requests are denied.</b>
""".strip()

grading_correct = """
<pre class="policy-code" style="font-family: 'Courier New', Courier, monospace; line-height: 1.2; white-space: pre-wrap; word-break: break-word;">
permits = {
  (<span class="request-subject">role</span> = Professor and <span class="request-action">act</span> = View) or
  (<span class="request-subject">role</span> = Professor and <span class="request-action">act</span> = Grade) or
  (<span class="request-subject">role</span> = TeachingAssistant and <span class="request-action">act</span> = View and <span class="request-resource">res</span> = Assignment) or
  (<span class="request-subject">role</span> = TeachingAssistant and <span class="request-action">act</span> = Grade and <span class="request-resource">res</span> = Assignment) or
  (<span class="request-subject">role</span> = Student and <span class="request-action">act</span> = View)
}

denies = {
  (<span class="request-subject">role</span> = Professor and <span class="request-resource">res</span>.submitted != True) or
  (<span class="request-subject">role</span> = TeachingAssistant and <span class="request-resource">res</span> = Assignment and <span class="request-resource">res</span>.submitted != True) or
  (<span class="request-subject">role</span> = TeachingAssistant and <span class="request-resource">res</span> = Exam) or
  (<span class="request-subject">role</span> = Student and <span class="request-resource">res</span> = Exam and <span class="request-resource">res</span>.submitted = True) or
  (<span class="request-subject">role</span> = Student and <span class="request-action">act</span> = Grade)
}
</pre>
""".strip()

grading_alt1 = """
<pre class="policy-code" style="font-family: 'Courier New', Courier, monospace; line-height: 1.2; white-space: pre-wrap; word-break: break-word;">
permits = {
  (<span class="request-subject">role</span> = Professor and <span class="request-action">act</span> = Grade) or
  (<span class="request-subject">role</span> = TeachingAssistant and <span class="request-action">act</span> = View and <span class="request-resource">res</span> = Assignment) or
  (<span class="request-subject">role</span> = Student and <span class="request-action">act</span> = View)
}

denies = {
  (<span class="request-subject">role</span> = Professor and <span class="request-resource">res</span>.submitted != True) or
  (<span class="request-subject">role</span> = TeachingAssistant and <span class="request-resource">res</span> = Assignment and <span class="request-resource">res</span>.submitted != True) or
  (<span class="request-subject">role</span> = TeachingAssistant and <span class="request-resource">res</span> = Exam) or
  (<span class="request-subject">role</span> = Student and <span class="request-resource">res</span> = Exam and <span class="request-resource">res</span>.submitted = True) or
  (<span class="request-subject">role</span> = Student and <span class="request-action">act</span> = Grade)
}
</pre>
""".strip()

grading_alt2 = """
<pre class="policy-code" style="font-family: 'Courier New', Courier, monospace; line-height: 1.2; white-space: pre-wrap; word-break: break-word;">
permits = {
  (<span class="request-subject">role</span> = Professor and <span class="request-action">act</span> = View) or
  (<span class="request-subject">role</span> = Professor and <span class="request-action">act</span> = Grade) or
  (<span class="request-subject">role</span> = TeachingAssistant and <span class="request-action">act</span> = View and <span class="request-resource">res</span> = Assignment) or
  (<span class="request-subject">role</span> = TeachingAssistant and <span class="request-action">act</span> = Grade and <span class="request-resource">res</span> = Assignment) or
  (<span class="request-subject">role</span> = Student and <span class="request-action">act</span> = View)
}

denies = {
  (<span class="request-subject">role</span> = TeachingAssistant and <span class="request-resource">res</span> = Assignment and <span class="request-resource">res</span>.submitted != True) or
  (<span class="request-subject">role</span> = TeachingAssistant and <span class="request-resource">res</span> = Exam) or
  (<span class="request-subject">role</span> = Student and <span class="request-resource">res</span> = Exam and <span class="request-resource">res</span>.submitted = True) or
  (<span class="request-subject">role</span> = Student and <span class="request-action">act</span> = Grade)
}
</pre>
""".strip()

grading_alt3 = """
<pre class="policy-code" style="font-family: 'Courier New', Courier, monospace; line-height: 1.2; white-space: pre-wrap; word-break: break-word;">
permits = {
  (<span class="request-subject">role</span> = Professor and <span class="request-action">act</span> = View) or
  (<span class="request-subject">role</span> = Professor and <span class="request-action">act</span> = Grade) or
  (<span class="request-subject">role</span> = TeachingAssistant and <span class="request-action">act</span> = View) or
  (<span class="request-subject">role</span> = TeachingAssistant and <span class="request-action">act</span> = Grade)
}

denies = {
  (<span class="request-subject">role</span> = Professor and <span class="request-resource">res</span>.submitted != True) or
  (<span class="request-subject">role</span> = TeachingAssistant and <span class="request-resource">res</span> = Assignment and <span class="request-resource">res</span>.submitted != True) or
  (<span class="request-subject">role</span> = Student and <span class="request-resource">res</span> = Exam and <span class="request-resource">res</span>.submitted = True) or
  (<span class="request-subject">role</span> = Student and <span class="request-action">act</span> = Grade)
}
</pre>
""".strip()


tech_description = """
<b>Network Admins can...</b>
  - access and edit the firewall.
  - access (but not edit) the server.
<b>System Admins can...</b>
  - access and edit the server.
  - access (but not edit) the firewall.

<b>Privileged actions cannot be performed after hours unless the subject is on call.</b>

<b>All other requests are denied.</b>
""".strip()

tech_correct = """
<pre class="policy-code" style="font-family: 'Courier New', Courier, monospace; line-height: 1.2; white-space: pre-wrap; word-break: break-word;">
permits = {
  (<span class="request-subject">role</span> = SystemAdmin and <span class="request-action">act</span> = Access and <span class="request-resource">res</span> = Server) or
  (<span class="request-subject">role</span> = SystemAdmin and <span class="request-action">act</span> = Edit and <span class="request-resource">res</span> = Server) or
  (<span class="request-subject">role</span> = SystemAdmin and <span class="request-action">act</span> = Access and <span class="request-resource">res</span> = Firewall) or
  (<span class="request-subject">role</span> = NetworkAdmin and <span class="request-action">act</span> = Access and <span class="request-resource">res</span> = Firewall) or
  (<span class="request-subject">role</span> = NetworkAdmin and <span class="request-action">act</span> = Edit and <span class="request-resource">res</span> = Firewall) or
  (<span class="request-subject">role</span> = NetworkAdmin and <span class="request-action">act</span> = Access and <span class="request-resource">res</span> = Server)
}

denies = {
  (<span class="request-action">act</span>.isPrivileged = True and <span class="request-resource">res</span>.isAfterHours = True and <span class="request-subject">sub</span>.isOnCall != True)
}
</pre>
""".strip()

tech_alt1 = """
<pre class="policy-code" style="font-family: 'Courier New', Courier, monospace; line-height: 1.2; white-space: pre-wrap; word-break: break-word;">
permits = {
  (<span class="request-subject">role</span> = SystemAdmin and <span class="request-action">act</span> = Access and <span class="request-resource">res</span> = Server) or
  (<span class="request-subject">role</span> = SystemAdmin and <span class="request-action">act</span> = Edit and <span class="request-resource">res</span> = Server) or
  (<span class="request-subject">role</span> = SystemAdmin and <span class="request-action">act</span> = Access and <span class="request-resource">res</span> = Firewall) or
  (<span class="request-subject">role</span> = NetworkAdmin and <span class="request-action">act</span> = Access and <span class="request-resource">res</span> = Firewall) or
  (<span class="request-subject">role</span> = NetworkAdmin and <span class="request-action">act</span> = Edit and <span class="request-resource">res</span> = Firewall) or
  (<span class="request-subject">role</span> = NetworkAdmin and <span class="request-action">act</span> = Access and <span class="request-resource">res</span> = Server)
}

denies = {
  (<span class="request-action">act</span>.isPrivileged = True and <span class="request-resource">res</span>.isAfterHours = True)
}
</pre>
""".strip()

tech_alt2 = """
<pre class="policy-code" style="font-family: 'Courier New', Courier, monospace; line-height: 1.2; white-space: pre-wrap; word-break: break-word;">
permits = {
  (<span class="request-subject">role</span> = SystemAdmin and <span class="request-action">act</span> = Access and <span class="request-resource">res</span> = Server) or
  (<span class="request-subject">role</span> = SystemAdmin and <span class="request-action">act</span> = Edit and <span class="request-resource">res</span> = Server) or
  (<span class="request-subject">role</span> = SystemAdmin and <span class="request-action">act</span> = Access and <span class="request-resource">res</span> = Firewall) or
  (<span class="request-subject">role</span> = NetworkAdmin and <span class="request-action">act</span> = Access and <span class="request-resource">res</span> = Firewall) or
  (<span class="request-subject">role</span> = NetworkAdmin and <span class="request-action">act</span> = Edit and <span class="request-resource">res</span> = Firewall) or
  (<span class="request-subject">role</span> = NetworkAdmin and <span class="request-action">act</span> = Access and <span class="request-resource">res</span> = Server) or
  (<span class="request-subject">sub</span>.isOnCall = True)
}

denies = {
  (<span class="request-action">act</span>.isPrivileged = True and <span class="request-resource">res</span>.isAfterHours = True and <span class="request-subject">sub</span>.isOnCall != True)
}
</pre>
""".strip()

tech_alt3 = """
<pre class="policy-code" style="font-family: 'Courier New', Courier, monospace; line-height: 1.2; white-space: pre-wrap; word-break: break-word;">
permits = {
  (<span class="request-subject">role</span> = SystemAdmin and <span class="request-action">act</span> = Access and <span class="request-resource">res</span> = Server) or
  (<span class="request-subject">role</span> = SystemAdmin and <span class="request-action">act</span> = Edit and <span class="request-resource">res</span> = Server) or
  (<span class="request-subject">role</span> = SystemAdmin and <span class="request-action">act</span> = Access and <span class="request-resource">res</span> = Firewall) or
  (<span class="request-subject">role</span> = NetworkAdmin and <span class="request-action">act</span> = Access and <span class="request-resource">res</span> = Firewall) or
  (<span class="request-subject">role</span> = NetworkAdmin and <span class="request-action">act</span> = Access and <span class="request-resource">res</span> = Server)
}

denies = {
  (<span class="request-subject">role</span> = NetworkAdmin and (<span class="request-action">act</span>.isPrivileged = True and 
      <span class="request-resource">res</span>.isAfterHours = True and <span class="request-subject">sub</span>.isOnCall != True))
}
</pre>
""".strip()


STUDY_PROBLEMS = [
    {
        "id": 0,
        "candidates": [
            "c",
            "a",
            "b",
            "d",
        ],
        "full_policies": {
            "c": accounting_correct,
            "a": accounting_alt1,
            "b": accounting_alt2,
            "d": accounting_alt3,
        },
        "description": accounting_description,
        "correct": "correct",
    },
    {
        "id": 1,
        "candidates": [
            "b",
            "c",
            "a",
            "d",
        ],
        "full_policies": {
            "c": grading_correct,
            "a": grading_alt1,
            "b": grading_alt2,
            "d": grading_alt3,
        },
        "description": grading_description,
        "correct": "c",
    },
    {
        "id": 2,
        "candidates": [
            "a",
            "d",
            "c",
            "b",
        ],
        "full_policies": {
            "c": tech_correct,
            "a": tech_alt1,
            "b": tech_alt2,
            "d": tech_alt3,
        },
        "description": tech_description,
        "correct": "c",
    },
]

SHOW_CANDIDATES = True
SHOW_LABELS = False
CONFIDENCE_THRESHOLD = 4
UNSURE_THRESHOLD = 6
ELIMINATION_THRESHOLD = 2
TESTING = True
