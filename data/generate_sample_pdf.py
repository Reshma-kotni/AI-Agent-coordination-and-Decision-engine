"""
generate_sample_pdf.py
──────────────────────
Generates a realistic vendor contract PDF for testing the PDFContractParserTool.
Run: python data/generate_sample_pdf.py
"""

from fpdf import FPDF
import os


def generate_contract_pdf(output_path: str = None):
    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), "sample_contract.pdf")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ── Page 1: Title & Parties ────────────────────────────────────────────────
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 15, "VENDOR SERVICE AGREEMENT", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, "Contract ID: CNT-2024-003", ln=True, align="C")
    pdf.cell(0, 8, "Effective Date: June 1, 2023", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "1. PARTIES", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6,
        'This Vendor Service Agreement ("Agreement") is entered into by and between:\n\n'
        "CLIENT: TechFlow Global Inc., a corporation organized under the laws of Delaware, "
        "with offices at 500 Innovation Drive, Suite 200, San Jose, CA 95134.\n\n"
        "VENDOR: Initech Solutions Pvt. Ltd., a company incorporated under the laws of India, "
        "with offices at Tower B, Cyber Gateway, HITEC City, Hyderabad, Telangana 500081.\n\n"
        "Collectively referred to as the 'Parties'."
    )
    pdf.ln(6)

    # ── Scope of Work ──────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "2. SCOPE OF WORK", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6,
        "The Vendor shall provide the following enterprise IT services:\n\n"
        "a) Development and maintenance of the Client's ERP integration layer.\n"
        "b) 24/7 production support with guaranteed 99.5% uptime SLA.\n"
        "c) Quarterly security audits and vulnerability assessments.\n"
        "d) Data migration services for legacy systems to cloud infrastructure.\n"
        "e) On-demand consulting for AI/ML feature development.\n\n"
        "All deliverables shall conform to the specifications outlined in Exhibit A "
        "(Statement of Work), which is incorporated herein by reference."
    )
    pdf.ln(6)

    # ── Contract Value & Payment ───────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "3. CONTRACT VALUE & PAYMENT TERMS", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6,
        "Total Contract Value: USD 150,000 (One Hundred Fifty Thousand US Dollars).\n\n"
        "Payment Schedule:\n"
        "- 20% upon execution of this Agreement (USD 30,000).\n"
        "- 30% upon completion of Phase 1 milestones (USD 45,000).\n"
        "- 30% upon completion of Phase 2 milestones (USD 45,000).\n"
        "- 20% upon final acceptance and go-live (USD 30,000).\n\n"
        "Payment Terms: Net 45 days from invoice date. Late payments shall accrue "
        "interest at 1.5% per month or the maximum rate permitted by law."
    )
    pdf.ln(6)

    # ── Page 2: Risk Clauses ───────────────────────────────────────────────────
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "4. INDEMNIFICATION & LIABILITY", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6,
        "4.1 The Vendor shall indemnify, defend, and hold harmless the Client from any "
        "claims, damages, losses, or expenses arising from:\n"
        "  (i) Breach of this Agreement by the Vendor;\n"
        "  (ii) Negligence or willful misconduct by Vendor personnel;\n"
        "  (iii) Infringement of third-party intellectual property rights.\n\n"
        "4.2 LIMITATION OF LIABILITY: In no event shall either Party's aggregate liability "
        "exceed the total Contract Value (USD 150,000). Neither Party shall be liable for "
        "indirect, incidental, consequential, or punitive damages.\n\n"
        "4.3 IMPORTANT: The indemnity cap specified in 4.2 does NOT apply to:\n"
        "  - Breaches of confidentiality or data protection obligations;\n"
        "  - Willful misconduct or fraud;\n"
        "  - IP infringement claims."
    )
    pdf.ln(6)

    # ── Termination ────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "5. TERMINATION", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6,
        "5.1 Either Party may terminate this Agreement for convenience upon 30 days' "
        "prior written notice to the other Party.\n\n"
        "5.2 Either Party may terminate immediately upon material breach by the other "
        "Party that remains uncured for 15 days after written notice.\n\n"
        "5.3 Upon termination, the Vendor shall:\n"
        "  (a) Immediately cease all work;\n"
        "  (b) Return or destroy all Client confidential information;\n"
        "  (c) Provide reasonable transition assistance for up to 30 days.\n\n"
        "NOTE: The short 30-day notice period and 15-day cure period may pose risk "
        "for complex enterprise engagements."
    )
    pdf.ln(6)

    # ── Data Protection ────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "6. DATA PROTECTION & COMPLIANCE", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6,
        "6.1 The Vendor acknowledges that it may process personal data on behalf of "
        "the Client and agrees to comply with all applicable data protection laws.\n\n"
        "6.2 WARNING: As of the execution date, no Data Processing Agreement (DPA) "
        "has been executed between the Parties. The Parties agree to negotiate and "
        "execute a DPA within 60 days of the Effective Date.\n\n"
        "6.3 The Vendor shall implement appropriate technical and organizational measures "
        "to ensure a level of security appropriate to the risk, including but not limited to:\n"
        "  - Encryption of data in transit and at rest;\n"
        "  - Regular security testing;\n"
        "  - Employee access controls and training.\n\n"
        "RISK FLAG: Absence of a signed DPA at contract commencement represents a "
        "GDPR compliance risk that requires immediate remediation."
    )
    pdf.ln(6)

    # ── Page 3: IP & Signatures ────────────────────────────────────────────────
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "7. INTELLECTUAL PROPERTY", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6,
        "7.1 All pre-existing intellectual property remains with the originating Party.\n\n"
        "7.2 DISPUTE: Ownership of newly developed IP under this Agreement is currently "
        "designated as 'shared ownership' between Client and Vendor. This ambiguous "
        "arrangement may lead to disputes regarding commercialization rights, licensing, "
        "and future modifications.\n\n"
        "7.3 RECOMMENDATION: The Parties should clarify IP ownership to designate all "
        "custom developments as 'work for hire' owned exclusively by the Client, with "
        "the Vendor retaining rights only to its pre-existing tools and frameworks."
    )
    pdf.ln(6)

    # ── SLA ─────────────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "8. SERVICE LEVEL AGREEMENT (SLA)", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6,
        "8.1 The Vendor guarantees 99.5% system uptime measured monthly.\n\n"
        "8.2 SLA penalties apply as follows:\n"
        "  - 99.0% - 99.49%: 5% credit on monthly invoice;\n"
        "  - 98.0% - 98.99%: 10% credit on monthly invoice;\n"
        "  - Below 98.0%: 15% credit and right to terminate.\n\n"
        "8.3 The SLA penalty cap is 5% of total contract value (USD 7,500), which is "
        "below industry standard of 10-15%. This low penalty cap reduces the Vendor's "
        "financial incentive to maintain service quality."
    )
    pdf.ln(6)

    # ── Governing Law ──────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "9. GOVERNING LAW & DISPUTE RESOLUTION", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6,
        "9.1 This Agreement shall be governed by the laws of the State of Maharashtra, India.\n\n"
        "9.2 Any disputes shall be resolved through binding arbitration administered by "
        "the Mumbai Centre for International Arbitration (MCIA).\n\n"
        "9.3 The prevailing Party in any arbitration shall be entitled to recover its "
        "reasonable attorneys' fees and costs."
    )
    pdf.ln(10)

    # ── Signatures ─────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "10. SIGNATURES", ln=True)
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 10)

    pdf.cell(90, 6, "For CLIENT: TechFlow Global Inc.", ln=False)
    pdf.cell(90, 6, "For VENDOR: Initech Solutions Pvt. Ltd.", ln=True)
    pdf.ln(10)

    pdf.cell(90, 6, "____________________________", ln=False)
    pdf.cell(90, 6, "____________________________", ln=True)
    pdf.cell(90, 6, "Name: Sarah Chen, VP Procurement", ln=False)
    pdf.cell(90, 6, "Name: Raj Patel, Managing Director", ln=True)
    pdf.cell(90, 6, "Date: June 1, 2023", ln=False)
    pdf.cell(90, 6, "Date: June 1, 2023", ln=True)

    pdf.output(output_path)
    print(f"Sample contract PDF generated: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_contract_pdf()
