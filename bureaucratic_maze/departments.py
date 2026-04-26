"""
Department definitions for the Bureaucratic Maze Navigator.
Defines all 10 departments, clerk personas, and response templates.
This module is SERVER-SIDE ONLY — never exposed to the agent.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import random


@dataclass(frozen=True)
class Department:
    dept_id: str
    name: str
    short_name: str
    clerk_name: str
    clerk_title: str
    floor: str
    description: str


# The 10 departments — fixed universe across all tasks
DEPARTMENTS: Dict[str, Department] = {
    "D1": Department(
        dept_id="D1",
        name="Reception and Enquiry Counter",
        short_name="Reception",
        clerk_name="Suresh",
        clerk_title="Junior Assistant",
        floor="Ground Floor, Counter 1",
        description="Entry point for all citizens. Handles initial queries and routing."
    ),
    "D2": Department(
        dept_id="D2",
        name="Documents Verification Cell",
        short_name="Documents Verification",
        clerk_name="Meenakshi Madam",
        clerk_title="Senior Verification Officer",
        floor="First Floor, Room 104",
        description="Verifies authenticity and completeness of submitted documents."
    ),
    "D3": Department(
        dept_id="D3",
        name="Revenue and Accounts Section",
        short_name="Revenue Section",
        clerk_name="Gopalan Sir",
        clerk_title="Accounts Officer",
        floor="Ground Floor, Room 12",
        description="Handles all financial matters — fees, refunds, tax assessments."
    ),
    "D4": Department(
        dept_id="D4",
        name="Records and Registry Office",
        short_name="Records Office",
        clerk_name="Lakshmi",
        clerk_title="Registry Clerk",
        floor="Second Floor, Room 201",
        description="Maintains official records — property, identity, addresses."
    ),
    "D5": Department(
        dept_id="D5",
        name="Field Inspection Unit",
        short_name="Field Inspection",
        clerk_name="Inspector Rajan",
        clerk_title="Field Inspector",
        floor="Ground Floor, Room 8 (Back)",
        description="Conducts physical verification and site inspections."
    ),
    "D6": Department(
        dept_id="D6",
        name="Senior Officer and Gazetted Officer Desk",
        short_name="Senior Officer Desk",
        clerk_name="Deputy Collector Sharma",
        clerk_title="Deputy Collector",
        floor="Third Floor, Room 301",
        description="Senior approvals, attestations, and authorizations."
    ),
    "D7": Department(
        dept_id="D7",
        name="Grievance Redressal Cell",
        short_name="Grievance Cell",
        clerk_name="Anitha",
        clerk_title="Grievance Officer",
        floor="First Floor, Room 110",
        description="Handles complaints, disputes, and appeals against department decisions."
    ),
    "D8": Department(
        dept_id="D8",
        name="State Portal and Help Desk",
        short_name="Portal Help Desk",
        clerk_name="Karthik",
        clerk_title="IT Support Officer",
        floor="Ground Floor, Kiosk Area",
        description="Assists with online forms, portal errors, and digital submissions."
    ),
    "D9": Department(
        dept_id="D9",
        name="Notary and Affidavit Counter",
        short_name="Notary Counter",
        clerk_name="Advocate Pillai",
        clerk_title="Notary Public",
        floor="Ground Floor, Room 3",
        description="Issues notarized documents, affidavits, and sworn statements."
    ),
    "D10": Department(
        dept_id="D10",
        name="Final Issuance Window",
        short_name="Issuance Window",
        clerk_name="Rajamani",
        clerk_title="Issuing Officer",
        floor="First Floor, Counter 7",
        description="The final window where approved documents and certificates are issued."
    ),
}


# Clerk response templates per department
# Each key is a situation type, value is a list of response variants (randomly chosen)

CLERK_RESPONSES: Dict[str, Dict[str, List[str]]] = {
    "D1": {
        "greeting": [
            "Naan Suresh, Reception-la irukken. Yenna venum? (I am Suresh at Reception. What do you need?)",
            "Yes yes, what is your problem? Please state your requirement quickly, there is a long queue.",
            "Welcome to the Municipal Office. Please state your purpose. Token number please?",
        ],
        "wrong_dept": [
            "Illa illa, adhu vera department. You have come to the wrong place. Please go to {correct_dept}.",
            "That matter is not handled here. This is only for enquiries. For your work, go to {correct_dept} on {floor}.",
            "Ayyo, why have you come here for that? Reception only does initial queries. Go to {correct_dept}.",
        ],
        "redirect": [
            "For this type of work, first you must go to {correct_dept}. Take token from there.",
            "Okay okay, I understand. First step — go to {correct_dept}. They will tell you next steps.",
            "Your file must go to {correct_dept} first. Without their stamp, no other department will accept.",
        ],
        "missing_doc": [
            "You need to bring {doc_name} also. Without that document, no use going anywhere.",
            "Enna? You don't have {doc_name}? That is mandatory. No processing without it.",
            "{doc_name} is compulsory for this. Please arrange and come back.",
        ],
        "wait": [
            "Sahib is not here right now. Please wait. He will come after lunch, around 2:30.",
            "System is slow today. Please take a seat. Maybe 20-30 minutes.",
            "Power went for some time, system restarting. Please wait outside.",
        ],
    },
    "D2": {
        "greeting": [
            "Documents section. Meenakshi here. Please submit your papers. I will verify.",
            "Yes, what documents do you have? Place them on the counter. I will check one by one.",
            "Documents Verification Cell. Please state your application number and submit originals.",
        ],
        "docs_incomplete": [
            "These documents are not sufficient. You are missing {missing_doc}. Come back with complete set.",
            "I cannot process without {missing_doc}. This is as per Rule 14(b). Please arrange.",
            "Verification cannot proceed. {missing_doc} is mandatory as per circular dated 14-03-2019.",
        ],
        "docs_not_attested": [
            "These documents are not attested. You need Gazetted Officer attestation on all copies.",
            "Original okay, but xerox copies must be self-attested. And {specific_doc} needs notarization.",
            "Without notarization from Notary Counter, I cannot accept this affidavit. Rule is rule.",
        ],
        "docs_accepted": [
            "Documents verified. Okay. Now take this receipt and go to {next_dept}.",
            "All documents in order. I am putting verification stamp. Next you must go to {next_dept}.",
            "Verified. File is forwarded. You can collect from {next_dept} after processing.",
        ],
        "second_visit_new_requirement": [
            "Wait — where is the {new_requirement}? Last time different officer was here. This is also required.",
            "Okay documents are correct but now I also need {new_requirement}. Circular came last week only.",
            "These were okay before but we have updated requirements. Now {new_requirement} is also mandatory.",
        ],
    },
    "D3": {
        "greeting": [
            "Accounts section. Gopalan here. Payment related? Or refund? What is the matter?",
            "Revenue section. State your query. Do you have the challan copy?",
            "Yes, Accounts department. What is your financial matter?",
        ],
        "denies_error": [
            "Our records show no discrepancy. The amount charged is correct as per assessment.",
            "Sir, we cannot just reverse charges based on your complaint. You must go to Grievance Cell first.",
            "I am not authorized to reverse any transaction without proper grievance reference number. Please go to D7 first.",
        ],
        "fee_required": [
            "For this service, fee of ₹{amount} is applicable. Please pay at counter and bring receipt.",
            "Processing fee is ₹{amount}. Cash or DD only. No UPI here, server problem.",
            "Challan must be paid — ₹{amount}. Take this form to bank, pay, bring receipt. Then only processing.",
        ],
        "refund_processing": [
            "Refund noted. I am entering in register. You will get acknowledgment from Issuance Window.",
            "Okay, reversal is being processed. Go to Final Issuance Window for your acknowledgment letter.",
            "File is updated. Refund will reflect in 7-10 working days. Collect acknowledgment from Counter 7.",
        ],
    },
    "D4": {
        "greeting": [
            "Records Office. Lakshmi speaking. What record do you need?",
            "Yes, Registry. Please state your survey number or application reference.",
            "Records and Registry. What is the purpose of your visit? Land records? Identity records?",
        ],
        "jargon_response": [
            "As per the gazette notification prerequisite under Section 12(3), the mutation entry requires prior encumbrance certificate. Have you obtained that?",
            "The khata extract must reflect the current assessment year. Your record shows legacy classification — revenue subdivision required before any modification.",
            "Without Form 7/12 extract showing clear title, registry cannot update records. Patta transfer also pending, I see.",
        ],
        "requires_doc": [
            "For address change in records, you need Aadhaar, electricity bill not older than 3 months, and property tax receipt.",
            "Name correction requires: original birth certificate, two affidavits, and gazette notification if name changed legally.",
            "For this entry, bring survey settlement register extract, encumbrance certificate, and property tax paid receipt.",
        ],
        "update_confirmed": [
            "Records updated. Here is the extract with correction. Keep this for further processing.",
            "Entry corrected in register. This certified copy is valid for 90 days for official purposes.",
            "Record updated. Certified extract issued. Please proceed to {next_dept} with this.",
        ],
    },
    "D5": {
        "greeting": [
            "Field Inspection Unit. Inspector Rajan. What inspection is required?",
            "Yes, Inspection Unit. Site visit? Or physical verification for document purpose?",
            "Rajan here. Inspection request? You need to fill Form FI-7 first.",
        ],
        "schedule_inspection": [
            "Inspection can be scheduled for next week. Inspector availability is limited. Come after {days} working days.",
            "I will note down the address. Inspection team will visit within {days} working days. You must be present.",
            "Site inspection request noted. Report will be ready in {days} working days after visit. Come back then.",
        ],
        "wait_state": [
            "Inspection completed. Report is being prepared. Come back after {days} working days to collect.",
            "Visit was done yesterday. Report is with senior inspector for signature. {days} more working days.",
            "Report is ready but not yet stamped by DIG office. Come back in {days} working days.",
        ],
        "inspection_passed": [
            "Inspection report is satisfactory. Here is the clearance certificate. Proceed to {next_dept}.",
            "Site verified. No violations found. Inspection clearance issued. Next go to {next_dept}.",
            "Physical verification complete. Report is positive. Take this and go to {next_dept} for approval.",
        ],
        "inspection_failed": [
            "Inspection found discrepancy. {issue}. Rectify and apply again.",
            "Site does not match submitted documents. {issue}. Cannot issue clearance.",
            "Report is negative. {issue}. File rejected. You may appeal at Grievance Cell.",
        ],
    },
    "D6": {
        "greeting": [
            "Deputy Collector's office. What is the matter? Do you have appointment?",
            "Senior Officer Desk. State your purpose. Attestation? Approval? What?",
            "Sharma here. What file do you have? Let me see the documents.",
        ],
        "needs_complete_file": [
            "File is incomplete. I need {missing_item} before I can sign. Come back with complete papers.",
            "I cannot approve without {missing_item}. Rules are clear. No shortcuts.",
            "Where is {missing_item}? Without that, my signature has no legal standing. Get it first.",
        ],
        "external_requirement": [
            "For structural changes, you need a licensed structural engineer's certificate. That is from a private engineer, not a government department. Get it and come back.",
            "NOC from {authority} is also required. That is not from us — you must obtain it separately.",
            "Medical fitness certificate must be from a registered doctor. Government hospital or empanelled private clinic. Not from here.",
        ],
        "approval_granted": [
            "File approved. Signature done. Proceed to {next_dept} for next step.",
            "Sanctioned. Here is the approval order. Take this to {next_dept}.",
            "Order passed. File is approved. Collect from my PA and go to {next_dept}.",
        ],
    },
    "D7": {
        "greeting": [
            "Grievance Cell. Anitha here. What is your complaint? Do you have previous reference number?",
            "Yes, Grievance Redressal. State your grievance. Against which department?",
            "Grievance office. What is the problem? Have you tried resolving at the concerned department first?",
        ],
        "needs_proof": [
            "For grievance against {dept}, you need proof of the error. Do you have {evidence}?",
            "Grievance noted. But to process, I need {evidence} as supporting document.",
            "Without {evidence}, I cannot formally register the grievance. Please obtain and submit.",
        ],
        "requires_inspection": [
            "For this type of dispute, site inspection is mandatory before we can process. Go to Field Inspection Unit first.",
            "Revenue disputes require physical verification. Get inspection clearance first, then come back.",
            "I cannot process without Field Inspection report. That is the standing order for all such cases.",
        ],
        "grievance_registered": [
            "Grievance registered. Reference number {ref}. Take this to {next_dept} for resolution.",
            "Complaint noted and forwarded to {next_dept}. Here is your acknowledgment.",
            "Your grievance is accepted. Go to {next_dept} with this reference. They must resolve within 30 days.",
        ],
    },
    "D8": {
        "greeting": [
            "Portal Help Desk. Karthik here. Online form problem? Or new registration?",
            "IT Support. What is the portal issue? Error code? Or form not submitting?",
            "Yes, Help Desk. System issue? Or you need help filling the online form?",
        ],
        "system_error": [
            "Ah yes, that form has a known bug. The date field is not accepting old dates. I will do backend entry manually.",
            "Portal is down for maintenance today. But I can do manual data entry. Give me your details.",
            "Error code {code} means duplicate entry in system. I will clear it. Give me your reference number.",
        ],
        "error_fixed": [
            "Done. I have cleared the error. Now resubmit the form — it should go through.",
            "System updated. Your application is now active. Go to {next_dept} with this acknowledgment.",
            "Manual entry done. Here is the system-generated reference. Proceed to {next_dept}.",
        ],
    },
    "D9": {
        "greeting": [
            "Notary Counter. Advocate Pillai. Affidavit? Or attestation? What do you need?",
            "Yes, Notary. What document needs to be notarized? Do you have the draft ready?",
            "Pillai here. Stamp paper needed? Or existing document to be notarized?",
        ],
        "affidavit_required": [
            "I need your original ID proof and two passport photos. Affidavit will be ready in 30 minutes.",
            "For this purpose, a sworn affidavit on ₹100 stamp paper is required. I can prepare it here. ₹200 charges.",
            "NOC affidavit requires your address proof also. Do you have it? Good. I will prepare.",
        ],
        "notarization_done": [
            "Affidavit prepared and notarized. Here is your copy. This is valid for 6 months.",
            "Document notarized. Seal affixed. You can proceed to {next_dept} with this.",
            "NOC affidavit is ready. Notarized copy — keep original safe. Go to {next_dept} now.",
        ],
    },
    "D10": {
        "greeting": [
            "Final Issuance Window. Rajamani here. What document are you collecting?",
            "Issuance Counter. Application number? Let me check if your file is ready.",
            "Yes, Counter 7. What is the purpose? Collection of approved document?",
        ],
        "file_not_ready": [
            "Your file has not reached here yet. Check back tomorrow. Or track on portal.",
            "Application is still processing at {pending_dept}. Not yet forwarded here.",
            "I don't have your file. Something is pending at {pending_dept}. Go check there.",
        ],
        "goal_achieved": [
            "All approvals received. Here is your {document_name}. Please sign the register.",
            "{document_name} is ready. Collect here. Keep this receipt for your records.",
            "Congratulations! Your {document_name} has been issued. Here you go. Have a good day.",
        ],
    },
}


def get_department(dept_id: str) -> Optional[Department]:
    return DEPARTMENTS.get(dept_id)


def get_clerk_response(dept_id: str, situation: str, **kwargs) -> str:
    """Get a clerk response for a given department and situation."""
    dept_responses = CLERK_RESPONSES.get(dept_id, {})
    templates = dept_responses.get(situation, [
        "Please wait. I will check and let you know.",
        "This matter needs to be verified. Come back later.",
        "I am not sure about this. Let me check with my senior.",
    ])
    template = random.choice(templates)
    try:
        return template.format(**kwargs)
    except KeyError:
        return template


def get_all_department_ids() -> List[str]:
    return list(DEPARTMENTS.keys())


def get_department_list() -> List[Dict]:
    """Public-facing department list (no internal details)."""
    return [
        {"id": d.dept_id, "name": d.name, "floor": d.floor}
        for d in DEPARTMENTS.values()
    ]
