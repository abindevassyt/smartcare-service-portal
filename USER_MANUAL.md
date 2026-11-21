# SmartCare Service Portal (MCSP-232)
## Comprehensive User Manual & Operations Guide

---

**Project Title**: SmartCare Service Portal  
**Course Code**: MCSP-232 (IGNOU MCA Project 2026)  
**Developer**: Abin Devassy Tharayil (Enrolment No: 2550779223)  
**Project Guide**: Anchitha G Babu  
**Technology Stack**: Python 3.11, Django 5.2, MySQL / SQLite, HTML5, CSS3, Vanilla JavaScript  

---

## Table of Contents
1. [System Overview & Architecture](#1-system-overview--architecture)
2. [Quick Start & Access Details](#2-quick-start--access-details)
3. [Consumer User Manual (Appliance Owners)](#3-consumer-user-manual-appliance-owners)
   - [3.1 Registration & Sign In](#31-registration--sign-in)
   - [3.2 Consumer Dashboard Overview](#32-consumer-dashboard-overview)
   - [3.3 Profile & Password Management](#33-profile--password-management)
   - [3.4 Authorized Service Centers Directory](#34-authorized-service-centers-directory)
   - [3.5 Appliance Registration & Activation Gate](#35-appliance-registration--activation-gate)
   - [3.6 Booking a Service / Repair Request](#36-booking-a-service--repair-request)
   - [3.7 Real-Time Work Order Tracking & Timeline](#37-real-time-work-order-tracking--timeline)
   - [3.8 Repair Estimate Approval & Cancellation](#38-repair-estimate-approval--cancellation)
   - [3.9 Service History & Invoice Access](#39-service-history--invoice-access)
   - [3.10 Logging Inquiries & Complaints](#310-logging-inquiries--complaints)
4. [Field Technician Operations Manual](#4-field-technician-operations-manual)
   - [4.1 Technician Dashboard & Work Queues](#41-technician-dashboard--work-queues)
   - [4.2 Consumer Account Verification Queue](#42-consumer-account-verification-queue)
   - [4.3 Appliance Verification & Activation Queue](#43-appliance-verification--activation-queue)
   - [4.4 Work Order Diagnostics Workbench](#44-work-order-diagnostics-workbench)
   - [4.5 Logging Defects & Symptoms](#45-logging-defects--symptoms)
   - [4.6 Spare Parts Consumption & Stock Deduction](#46-spare-parts-consumption--stock-deduction)
   - [4.7 Step-by-Step Activity Logging](#47-step-by-step-activity-logging)
   - [4.8 Automated Billing Engine & Invoice Generation](#48-automated-billing-engine--invoice-generation)
   - [4.9 Reference Catalogs & Directory Views](#49-reference-catalogs--directory-views)
5. [Administrator Operations Manual](#5-administrator-operations-manual)
   - [5.1 Admin Dashboard Overview](#51-admin-dashboard-overview)
   - [5.2 Master Data CRUD Management](#52-master-data-crud-management)
   - [5.3 Onboarding Service Centers & Technicians](#53-onboarding-service-centers--technicians)
   - [5.4 Registered Appliances Oversight](#54-registered-appliances-oversight)
   - [5.5 Work Order Management & Technician Assignment](#55-work-order-management--technician-assignment)
   - [5.6 Work Order Diagnostic Inspection](#56-work-order-diagnostic-inspection)
   - [5.7 Customer Complaints Resolution](#57-customer-complaints-resolution)
   - [5.8 Management Reports Hub & CSV Exports](#58-management-reports-hub--csv-exports)
6. [Formal Printable Service Invoice Guide](#6-formal-printable-service-invoice-guide)
7. [System Security, Error Codes & Troubleshooting](#7-system-security-error-codes--troubleshooting)

---

## 1. System Overview & Architecture

The **SmartCare Service Portal** is an end-to-end after-sales appliance service management web application designed for consumer electronics and home appliance manufacturers. It connects three core stakeholders into a unified digital ecosystem:

```
               ┌────────────────────────────────────────────────────────┐
               │              SmartCare Service Portal                  │
               └───────┬──────────────────────┬──────────────────┬──────┘
                       │                      │                  │
                       ▼                      ▼                  ▼
              ┌────────────────┐     ┌────────────────┐   ┌───────────────┐
              │  Consumer      │     │  Technician    │   │ Administrator │
              │  Self-Service  │     │  Workbench     │   │ Management    │
              └────────────────┘     └────────────────┘   └───────────────┘
```

### Core Business Pillars
1. **Appliance Activation Gate**: Newly purchased appliances entered by consumers remain in `Pending` state until verified by a technician. Service tickets can only be booked for verified, active appliances.
2. **Automated Warranty Engine**: Automatically evaluates appliance warranty validity in real-time by comparing ticket creation date against `warnt_enddate`.
3. **Transparent Out-of-Warranty Approval**: If an estimate is prepared for an out-of-warranty appliance, the consumer receives an instant digital quotation with one-click **Accept Estimate** or **Cancel Order** actions.
4. **Atomic Spare Parts Inventory**: Technicians consume spare parts directly within the work order workbench; available inventory is strictly checked and deducted atomically within database transaction blocks.
5. **Rule-Based Automated Invoicing**: Calculates labor fees and spare part costs according to 3 strict business rules:
   - **Rule 1 (In Warranty)**: Total Amount = ₹0.00; if irreparable, automatically escalates for Warranty Replacement.
   - **Rule 2 (Out of Warranty & Irreparable)**: Total Amount = ₹0.00 (No-charge diagnostic policy).
   - **Rule 3 (Out of Warranty & Repaired)**: Total Amount = Sum of Spare Parts + Technician Labor Fee.

---

## 2. Quick Start & Access Details

### System Access
- **Local Browser URL**: `http://127.0.0.1:8000/` or `http://localhost:8000/`
- **Local Network URL**: `http://192.168.1.41:8000/` (Accessible on phones/tablets connected to the same Wi-Fi network)

### Pre-Configured System Credentials

| Role | Username / Email | Password | Preloaded Context |
|---|---|---|---|
| **Administrator** | `admin` | `admin123` | Master control over master data, technician assignments, reports, and complaints. |
| **Technician** | `rahul.tech`<br>*(or `rahul.tech@smartcare.com`)* | `password123` | Assigned to Central Hub; has assigned service orders, activation queues, and inventory tools. |
| **Consumer** | `consumer`<br>*(or `consumer@smartcare.com`)* | `password123` | Consumer *Anjali Nair*; has a registered Double Door Fridge and active Work Order #10001. |

> [!TIP]
> You can also register a brand new consumer at any time by clicking **"Register Account"** on the login page (`/register/`).

---

## 3. Consumer User Manual (Appliance Owners)

The Consumer Portal provides customers with self-service transparency over their home appliances, warranty protections, repair bookings, and billing history.

```
                  CONSUMER JOURNEY WORKFLOW
  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │ 1. Register  │ ──► │ 2. Add       │ ──► │ 3. Technician│
  │    Account   │     │    Appliance │     │    Activation│
  └──────────────┘     └──────────────┘     └──────┬───────┘
                                                   │
  ┌──────────────┐     ┌──────────────┐     ┌──────▼───────┐
  │ 6. Printable │ ◄── │ 5. Timeline  │ ◄── │ 4. Book      │
  │    Invoice   │     │    Tracking  │     │    Repair    │
  └──────────────┘     └──────────────┘     └──────────────┘
```

### 3.1 Registration & Sign In
1. Navigate to `http://127.0.0.1:8000/login/`.
2. Click **"Register here"** at the bottom of the login card.
3. Complete the registration form:
   - **Personal Details**: First Name, Last Name, Date of Birth.
   - **Contact Information**: Primary Mobile Number, Secondary Phone, Email Address.
   - **Location**: Select **State** (e.g., Kerala). The **District** dropdown will automatically populate dynamically with authorized districts via live API.
   - **Address**: House Name / Street Address, PIN Code.
   - **Security**: Enter and confirm your account password.
4. Click **"Complete Registration"**. Your profile is created, and you are redirected to the unified login screen.
5. Log in using your registered email address and password.

### 3.2 Consumer Dashboard Overview
Upon logging in, the **Consumer Dashboard** (`/consumer-dashboard/`) presents:
- **KPI Summary Cards**:
  - *Total Appliances*: Count of all registered appliances.
  - *Active Service Requests*: Open tickets currently being inspected or serviced.
  - *Completed Services*: Number of successfully resolved work orders.
  - *Expiring Soon (30 Days)*: Visual warning if any appliance warranty expires within a month.
- **My Registered Appliances Grid**: Overview of registered appliances with calculated warranty status badges (`In Warranty` vs `Out of Warranty`).
- **Active Service Requests**: Real-time listing of active tickets with status badges and quick links to view progress timelines.

### 3.3 Profile & Password Management
1. Click **"My Profile"** in the sidebar navigation (`/consumer/profile/`).
2. **Update Details**: Update your residential address, contact numbers, state, or district.
3. **Change Password**: Enter your new password and confirmation to update credentials securely with PBKDF2 hashing.

### 3.4 Authorized Service Centers Directory
1. Click **"Find Service Centers"** (`/consumer/service-centers/`).
2. Filter centers by selecting your **State** and **District**.
3. The directory displays:
   - Service Center Name and Address.
   - Contact Person and Official Landline Phone.
   - Urgent Mobile Number and Support Email.
   - Operating Status badge (`Active`).

### 3.5 Appliance Registration & Activation Gate
To protect against fraudulent claims, appliances registered online start in `Pending` state and must be verified by service staff before service tickets can be opened:

1. Click **"Register Appliance"** (`/services/consumer/products/`).
2. Fill in the purchase verification form:
   - **Product Model**: Choose the appliance from the dropdown (e.g., *Double Door Fridge RF-260D*).
   - **Serial Number (`prod_no`)**: Enter the unique serial number found on the product barcode label.
   - **Warranty Card Number**: Enter the warranty registration number from the physical warranty card.
   - **Purchase Invoice Number**: Enter the tax invoice number issued by the retailer.
   - **Invoice Date**: Select the exact purchase date.
   - **Warranty End Date**: Select the warranty expiration date (typically 1 to 5 years from invoice date).
3. Click **"Register Appliance"**.
4. The appliance will appear in your **Registered Appliances** list with a yellow **"Pending Activation"** badge.
5. Once a technician verifies the purchase proof in their queue, the badge changes to a green **"Active"** badge, unlocking service bookings.

### 3.6 Booking a Service / Repair Request
1. Click **"Book Service"** (`/services/consumer/book-service/`).
2. **Select Verified Appliance**: Choose any appliance with an `Active` status from the dropdown. (Appliances marked `Pending` are intentionally disabled by the activation gate).
3. **Service Location Type**:
   - `Home Service`: Field technician visits your residence (recommended for washing machines, refrigerators, large TVs).
   - `Carry In`: You drop off the appliance at the authorized service hub.
4. **Call / Service Type**: Select `Repair`, `Installation`, `Maintenance`, or `Warranty Inspection`.
5. **Issue Description**: Provide specific symptoms (e.g., *"Refrigerator cooling coil frosting over; compressor runs continuously without cooling"*).
6. Click **"Confirm Service Request"**.
7. The system instantly generates a unique **Service Request Number (`Serv_req_no`)**, sets initial status to `Pending`, and routes the order to the Administrator assignment queue.

### 3.7 Real-Time Work Order Tracking & Timeline
1. Click **"Track Orders"** (`/services/consumer/track-orders/`).
2. Click **"View Full Timeline"** on any active or completed ticket (`/services/consumer/track-orders/<w_orderid>/`).
3. The detail workbench displays:
   - **Appliance Information**: Category, model, serial number, and live calculated warranty badge (`In Warranty` vs `Out of Warranty`).
   - **Assigned Technician Details**: Name, mobile phone, and qualification of the technician assigned to your ticket.
   - **Promised Delivery Date**: Expected resolution date set by the technician.
   - **Technician Diagnostics Block**: Shows technical defect description, unit condition upon arrival, and observed symptoms.
   - **Chronological Activity Timeline**: Detailed audit trail showing every update logged by the technician (e.g., *"Inspection completed"*, *"Parts replaced"*, *"Final load testing"*).

### 3.8 Repair Estimate Approval & Cancellation
If your appliance is **Out of Warranty** and requires paid spare parts or labor:
1. When the technician or admin sets an estimate, the work order status shifts to **"Estimate Sent"**.
2. Open the ticket tracking screen (`/services/consumer/track-orders/<w_orderid>/`).
3. A prominent **Repair Estimate Notification Banner** appears with:
   - Estimated Repair Cost: e.g., `₹1,250.00`.
   - Explanation of parts and labor charges.
4. **Choose Action**:
   - **"Accept Estimate & Proceed"**: Confirms your consent. The ticket status updates to `Assigned` / `In Progress`, technician is notified, and repair begins.
   - **"Cancel Request"**: Rejects the estimate. The ticket status updates to `Cancelled` with zero charges applied.

### 3.9 Service History & Invoice Access
1. Click **"Service History"** (`/services/consumer/history/`).
2. Displays a consolidated table of all historical tickets, completion dates, and finalized invoice amounts.
3. For any completed work order, click **"View & Print Invoice"** to open the formal tax invoice with printable letterhead.

### 3.10 Logging Inquiries & Complaints
1. Click **"Complaints & Feedback"** (`/services/consumer/complaints/`).
2. Select the registered appliance and enter your subject and detailed complaint message (e.g., delay in service, recurring defect).
3. Track the ticket status:
   - `Open`: Awaiting administrative review.
   - `Resolved`: Administrator has reviewed and posted an official service resolution reply.

---

## 4. Field Technician Operations Manual

The Technician Module is a high-efficiency diagnostic and field management workspace designed to accelerate ticket resolution, verify warranty credentials, record defects, consume spare parts, and automate billing.

```
                 TECHNICIAN REPAIR LIFECYCLE
  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │ 1. Assigned  │ ──► │ 2. Log       │ ──► │ 3. Consume   │
  │    Ticket    │     │    Defect    │     │    Spare Part│
  └──────────────┘     └──────────────┘     └──────┬───────┘
                                                   │
  ┌──────────────┐     ┌──────────────┐     ┌──────▼───────┐
  │ 6. Closed /  │ ◄── │ 5. Automated │ ◄── │ 4. Complete  │
  │    Invoiced  │     │    Billing   │     │    Testing   │
  └──────────────┘     └──────────────┘     └──────────────┘
```

### 4.1 Technician Dashboard & Work Queues
Upon signing in as a technician (`/tech-dashboard/`), your workspace displays:
- **KPI Summary Tiles**:
  - *Assigned Jobs*: Count of tickets currently assigned to you.
  - *In-Progress*: Tickets actively under diagnosis or bench repair.
  - *Pending Consumer Approvals*: Consumers awaiting verification.
  - *Pending Appliance Verifications*: New registrations awaiting warranty proof validation.
- **Grouped Work Order Queues**:
  - Tab 1: **Assigned** (New jobs requiring initial inspection).
  - Tab 2: **In Progress** (Units currently undergoing bench work or testing).
  - Tab 3: **Spare Parts Pending** (Awaiting stock arrival).
  - Tab 4: **Completed** (Finalized and invoiced jobs).

### 4.2 Consumer Account Verification Queue
1. Click **"Consumer Activations"** in the sidebar (`/tech/activate-consumers/`).
2. Review newly registered consumer profiles (Name, Mobile, State, District, Registration Date).
3. Inspect profile authenticity and click **"Activate Consumer"** to toggle their account status to `Active`.

### 4.3 Appliance Verification & Activation Queue
1. Click **"Product Activations"** (`/services/tech/activate-products/`).
2. Review customer-submitted appliance registrations:
   - Product Model Name and Category.
   - Serial Number (`prod_no`).
   - Warranty Card Number (`warnt_cardno`).
   - Retailer Invoice Number and Purchase Date.
   - Calculated Warranty Coverage period.
3. Click **"Verify & Activate"** (`tech_activate_product_toggle`).
4. This unlocks service bookings for the customer on that verified appliance.

### 4.4 Work Order Diagnostics Workbench
Click **"Open Workbench"** on any assigned job (`/services/tech/work-order/<w_orderid>/`) to access the 4-panel control center:

#### Panel 1: Status & Schedule Management
- **Work Status**: Update ticket state (`In Progress`, `Spare Parts Pending`, `Completed`, `Irreparable`).
- **Jobsheet Type**: Classify work (`Standard Repair`, `Major Overhaul`, `Warranty Replacement`, `Preventive Maintenance`).
- **Promised Delivery Date**: Enter the committed completion date for customer visibility.
- **Progress Remark**: Add technician field notes.
- Click **"Update Status & Schedule"**.

### 4.5 Logging Defects & Symptoms
Under Panel 2 (**"Diagnostic Defect & Symptom Entry"**):
1. **Defect Name**: Technical classification (e.g., *Burnt Motor Run Capacitor*, *Thermostat Sensor Drift*).
2. **Defect Description**: Specific component failure notes.
3. **Appliance Condition**: Physical condition of the unit upon inspection (e.g., *Good*, *Heavily Scaled*, *External Dents*).
4. **Observed Symptom**: Visible malfunction (e.g., *Drum not rotating; humming sound emitted*).
5. **Repair Required**: Planned corrective measure (e.g., *Replace Capacitor and test winding resistance*).
6. **Faulty Status**: Select `Yes` if defective component identified.
7. **Repaired**: Choose `Yes` (if repairable) or `No` (if irreparable).
8. Click **"Record Defect Diagnostic"** to save into [`DefectsSymptom`](file:///c:/Users/Abin/Desktop/MCA_Projects/smartcare_project/services/models.py#L86-L100).

### 4.6 Spare Parts Consumption & Stock Deduction
Under Panel 3 (**"Spare Parts Allocation & Stock Deduction"**):
1. **Select Spare Part**: Choose the replacement component from the dropdown (shows live stock quantity and unit rate).
2. **Quantity (`Qty`)**: Enter the quantity consumed.
3. **Usage Details**:
   - *Reason*: `Replacement`, `Refurbishment`, or `Warranty Claim`.
   - *Unit Section*: Section of appliance (e.g., `Compressor Compartment`, `Display PCB`, `Drive Assembly`).
   - *Position*: `Internal` or `External`.
4. Click **"Allocate & Deduct Inventory"**.
5. **System Validation**:
   - If `Requested Qty > Available Stock`, transaction is aborted with:
     > *"Insufficient inventory for Part XYZ. Available stock is 2, but 5 was requested."*
   - If stock is sufficient, the system atomically updates [`SparePart.qty`](file:///c:/Users/Abin/Desktop/MCA_Projects/smartcare_project/products/models.py#L42) within `@transaction.atomic` and logs records in [`ServicePart`](file:///c:/Users/Abin/Desktop/MCA_Projects/smartcare_project/services/models.py#L102) and [`ServicePartDtls`](file:///c:/Users/Abin/Desktop/MCA_Projects/smartcare_project/services/models.py#L112).

### 4.7 Step-by-Step Activity Logging
Under Panel 4 (**"Step-by-Step Activity History"**):
- Enter real-time audit updates (e.g., *"Unit received at bench; disassembly begun"*, *"Motor windings tested: 24 Ohms normal"*).
- Click **"Add Activity Log"** to append timestamped entries to [`ActivityDtls`](file:///c:/Users/Abin/Desktop/MCA_Projects/smartcare_project/services/models.py#L76).

### 4.8 Automated Billing Engine & Invoice Generation
When repairs are completed, click **"Proceed to Billing & Invoicing"** (`/services/tech/generate-invoice/<w_orderid>/`):

```
                     AUTOMATED BILLING LOGIC
                   Is Appliance In-Warranty?
                         /           \
                     YES               NO
                     /                   \
        Amount = ₹0.00             Was it Repaired?
     (If Irreparable:              /              \
      Escalate for               YES               NO
      Replacement)               /                   \
                   Amount = Parts + Labor       Amount = ₹0.00
                   Status = Completed           Status = Irreparable
```

1. Select **Was Appliance Repaired?**:
   - `Yes (Successfully Repaired)`
   - `No (Irreparable)`
2. Enter **Technician Labor / Service Charge** (Default: `₹350.00`).
3. The system executes automated billing rules:
   - **Rule 1 (In Warranty)**:
     - Regardless of parts consumed or labor charge, final `Amount = 0.00`.
     - If marked `Repaired = No`, jobsheet type updates to `'Warranty Replacement'`.
   - **Rule 2 (Out of Warranty & Irreparable)**:
     - Company no-charge policy: `Amount = 0.00`, ticket status becomes `'Irreparable'`.
   - **Rule 3 (Out of Warranty & Repaired)**:
     - `Amount = Sum(ServicePartDtls.Qty * SparePart.price) + Service Charge`.
4. Click **"Generate Official Invoice"**.
5. The invoice is generated in [`ServiceInvoice`](file:///c:/Users/Abin/Desktop/MCA_Projects/smartcare_project/services/models.py#L121), the work order is marked `Completed` with `close_date` stamped, and the printable invoice link becomes available.

### 4.9 Reference Catalogs & Directory Views
Technicians have read-only access to master data from the sidebar:
- **Products Catalog** (`/products/tech/products/`): Browse categories, specifications, and model numbers.
- **Spare Parts Inventory** (`/products/tech/spare-parts/`): View live stock counts with low-stock badges.
- **Service Centers** (`/accounts/tech/service-centers/`): Directory of authorized centers.
- **Technicians Directory** (`/accounts/tech/technicians/`): Colleague contact phone and mobile directory.

---

## 5. Administrator Operations Manual

The Administrator Module gives service managers full operational control over master data catalogs, technician dispatching, customer support resolution, and business intelligence reporting.

### 5.1 Admin Dashboard Overview
Access the central dashboard at `/admin-dashboard/`:
- **Real-Time KPIs**:
  - *Total Registered Consumers*: Active consumer base.
  - *Active Service Centers*: Operational authorized hubs.
  - *Pending Work Orders*: New tickets awaiting technician assignment.
  - *Active Field Technicians*: Certified technicians available for dispatch.
  - *Low Stock Parts Alerts*: Count of spare parts with inventory `< 5` units.
- **Quick-Action Dispatch Table**: Recent work orders showing request number, appliance model, current status, and assigned technician.

### 5.2 Master Data CRUD Management
Manage all core operational entities from the left sidebar:

#### 1. States & Districts (`/admin/manage/states/`, `/admin/manage/districts/`)
- Add new administrative states (e.g., *Kerala, Tamil Nadu, Karnataka*).
- Add districts mapped to their respective parent state.
- Supports search, editing, and protected deletion (deletion blocked if dependent service centers or consumers exist).

#### 2. Authorized Service Centers (`/admin/manage/service-centers/`)
- Register new regional centers with Center Name, State, District, Contact Person, Phone, Mobile, Email, and Operating Status (`Active` / `Inactive`).
- Manage credentials for center logins.

#### 3. Product Categories & Products (`/admin/manage/categories/`, `/admin/manage/products/`)
- Define product categories (e.g., *Television, Refrigerator, Washing Machine, Microwave Oven*).
- Register appliances with Model Number, Unique Serial Format, Retail Price, Description, and Product Photo image upload.

#### 4. Spare Parts Inventory (`/admin/manage/spare-parts/`)
- Add replacement parts linked to product models.
- Set unit sale price and initial stock quantity.
- Real-time stock alerts highlight parts with low inventory in amber/red badges.

#### 5. Work Statuses (`/admin/manage/statuses/`)
- Manage lifecycle stages (`Pending`, `Assigned`, `In Progress`, `Spare Parts Pending`, `Completed`, `Irreparable`, `Cancelled`).

### 5.3 Onboarding Service Centers & Technicians
Register new field technicians (`/admin/manage/technicians/`):
1. Enter Technician Full Name, Residential Address, State, District, Gender, Qualification, and Experience.
2. Enter Mobile Number and Email Address (e.g., `suresh.tech@smartcare.com`).
3. Set login password (default: `password123`).
4. Click **"Register Technician"**.
5. The system performs an atomic dual-table insertion:
   - Creates the [`Technician`](file:///c:/Users/Abin/Desktop/MCA_Projects/smartcare_project/accounts/models.py#L91) master profile record.
   - Creates the [`AuthUser`](file:///c:/Users/Abin/Desktop/MCA_Projects/smartcare_project/accounts/models.py#L113) login credentials with role `'Technician'`.

### 5.4 Registered Appliances Oversight
Navigate to **"Consumer Appliances"** (`/admin/consumer-products/`):
- View all customer-registered appliances across all regions.
- Real-time warranty engine indicates whether each appliance is `In Warranty` or `Out of Warranty`.
- Inspect serial numbers, warranty card numbers, and invoice purchase dates.
- Admin can manually override activation status (`Pending` vs `Active`).

### 5.5 Work Order Management & Technician Assignment
Navigate to **"Manage Work Orders"** (`/admin/work-orders/`):
1. Locate incoming tickets in `Pending` state.
2. Click **"Assign & Update"** (`/admin/work-orders/<w_orderid>/assign/`).
3. **Dispatch Fields**:
   - **Assign Technician**: Select an active field technician from the dropdown.
   - **Repair Estimate (`Inv_amt`)**: Enter estimated repair cost if out of warranty.
   - **Status**: Change status to `Assigned` or `Estimate Sent`.
   - **Promised Delivery Date**: Set committed resolution date.
   - **Internal Remark**: Enter assignment notes.
4. Click **"Update Assignment"**.
5. Ticket is dispatched, the assigned technician sees it on their workbench, and an audit trail entry is recorded in [`ActivityDtls`](file:///c:/Users/Abin/Desktop/MCA_Projects/smartcare_project/services/models.py#L76).

### 5.6 Work Order Diagnostic Inspection
Click **"Inspect Work Order"** (`/admin/work-orders/<w_orderid>/details/`):
- Review comprehensive diagnostic findings submitted by the technician.
- View component defects recorded in [`DefectsSymptom`](file:///c:/Users/Abin/Desktop/MCA_Projects/smartcare_project/services/models.py#L86).
- Audit consumed replacement spare parts and unit charges in [`ServicePartDtls`](file:///c:/Users/Abin/Desktop/MCA_Projects/smartcare_project/services/models.py#L112).
- View complete timestamped history of actions.

### 5.7 Customer Complaints Resolution
Navigate to **"Manage Complaints"** (`/admin/complaints/`):
1. Review open consumer inquiries and grievances.
2. Click **"Review & Reply"** (`/admin/complaints/<id>/reply/`).
3. Read customer remarks and registered appliance history.
4. Enter official service resolution remarks in **Service Reply**.
5. Set ticket status to `Resolved`.
6. Click **"Submit Official Reply"**. The consumer is immediately notified on their portal.

### 5.8 Management Reports Hub & CSV Exports
Navigate to **"Management Reports"** (`/admin/reports/`) to access 4 dedicated analytical modules with real-time CSV streaming:

```
                      ADMIN REPORTS HUB
  ┌────────────────────────────────────────────────────────┐
  │  Tab 1: Service Centers Report (by State & District)   │
  ├────────────────────────────────────────────────────────┤
  │  Tab 2: Consumer Registrations Report (by Date & State)│
  ├────────────────────────────────────────────────────────┤
  │  Tab 3: Appliances & Warranty Report (by Category)     │
  ├────────────────────────────────────────────────────────┤
  │  Tab 4: Work Orders & Revenue Report (by Tech & Status)│
  └────────────────────────────────────────────────────────┘
```

#### Tab 1: Authorized Service Centers Report
- **Filters**: State, District, Status (`Active` / `Inactive`).
- **Metrics**: Total centers, active hubs count.
- **Action**: Click **"Export CSV"** to download `service_centers_report_<date>.csv`.

#### Tab 2: Consumer Registrations Report
- **Filters**: State, Registration Status (`Pending` / `Active`), Date Range (`From Date` to `To Date`).
- **Metrics**: Total consumers registered, pending verifications.
- **Action**: Click **"Export CSV"** to download `consumer_registrations_report_<date>.csv`.

#### Tab 3: Registered Appliances & Warranty Expiry Report
- **Filters**: Product Category, Activation Status, Warranty Status (`In Warranty` vs `Expired`).
- **Live Calculation**: Compares current date against `warnt_enddate` dynamically.
- **Action**: Click **"Export CSV"** to download `appliances_warranty_report_<date>.csv`.

#### Tab 4: Work Orders Lifecycle & Invoiced Revenue Report
- **Filters**: Date Range, Assigned Technician, Ticket Status, Service Location Type (`Home Service` vs `Carry In`).
- **Financial Metrics**: Real-time aggregation of **Total Invoiced Revenue (₹)** across all completed tickets.
- **Action**: Click **"Export CSV"** to download `work_orders_report_<date>.csv`.

---

## 6. Formal Printable Service Invoice Guide

The printable tax invoice (`/invoice/<invoice_id>/print/`) complies with commercial consumer electronics service billing standards.

### Invoice Layout Breakdown
1. **Header & Service Center Letterhead**:
   - Authorized Service Center Name, Address, City, PIN.
   - Contact Person, Landline Phone, Mobile Number, Official Email.
   - Official GSTIN / Tax Identification.
2. **Metadata Bar**:
   - Tax Invoice Number and Invoice Date.
   - Work Order ID (`W_orderid`) and Service Request Number (`Serv_req_no`).
   - Service Mode (`Home Service` / `Carry In`) and Call Type (`Repair` / `Maintenance`).
3. **Consumer & Appliance Specification Block**:
   - Customer Full Name, Mobile Number, Email, Full Service Address.
   - Appliance Model Name, Category, Serial Number (`prod_no`), Warranty Card Number.
   - Real-Time Warranty Validity Badge (`In Warranty` vs `Out of Warranty`).
4. **Diagnostic Findings Summary**:
   - Defect classification, observed symptom, and unit condition upon arrival.
5. **Itemized Consumed Spare Parts Table**:
   - Part Name and Serial Code.
   - Quantity Consumed (`Qty`).
   - Unit Rate (₹).
   - Line Item Subtotal (₹).
6. **Financial Breakdown Summary**:
   - Spare Parts Subtotal (₹).
   - Technician Labor / Service Charge (₹).
   - Warranty Coverage Discount (₹).
   - **Grand Total Payable (₹)**.
   - *Prominent Callout*: If under valid warranty, displays bold **"ZERO CHARGE (WARRANTY COVERED) — ₹0.00"** banner.
7. **Signatures & Legal Disclaimer**:
   - Authorized Technician Signoff Box.
   - Customer Acknowledgement Signoff Box.
   - Official terms and warranty disclaimer.

### Print Instructions
- Press `Ctrl + P` (Windows) or click **"Print / Save PDF"** button at the top right of the screen.
- High-fidelity `@media print` CSS will automatically:
  - Hide navigation bars, headers, and action buttons.
  - Set margins to standard A4 dimensions.
  - Remove drop-shadows and format backgrounds for crisp monochrome or color laser printing.
  - Output cleanly to physical paper or PDF.

---

## 7. System Security, Error Codes & Troubleshooting

### Security Safeguards
1. **Session-Based Role-Based Access Control (RBAC)**:
   - Protected with custom Python decorators: `@admin_required`, `@tech_required`, and `@consumer_required`.
   - Prevents unauthorized cross-role access (e.g., Consumers cannot access technician workbenches or admin reports).
2. **Ownership Validation**:
   - Printable invoices and service order timelines strictly verify that the logged-in consumer owns the appliance; attempts to view other consumers' invoices trigger an HTTP 403 Forbidden response.
3. **Password Security**:
   - Passwords stored using PBKDF2 with SHA-256 hash algorithms.
4. **Database Integrity**:
   - Multi-step operations (Technician creation with AuthUser, Spare parts deduction with Work Order logging, Invoice generation) are protected by `@transaction.atomic` blocks to prevent partial writes.

### Common Error Codes & Resolution

| Error / Notice | Cause | Resolution |
|---|---|---|
| **403 Forbidden** | Attempted to access an administrative or technician screen without proper privileges. | Ensure you are logged into an account with the required role. |
| **404 Not Found** | The requested work order, appliance, or invoice ID does not exist in the database. | Return to dashboard and verify the ID from the list. |
| **"Cannot book service for pending appliance"** | Attempted to book repair for newly registered appliance that has not been approved. | Contact technician/admin to verify purchase proof and activate the appliance in `/services/tech/activate-products/`. |
| **"Insufficient inventory for part XYZ"** | Technician attempted to allocate more spare parts than currently in stock. | Admin must update stock quantity in `/admin/manage/spare-parts/`. |
| **Login Redirect Loop** | Logging in while another session is already cached in browser. | Click **"Sign Out"** from the top right user menu and log in with the desired role. |

---

## Conclusion & Project Verification

The **SmartCare Service Portal** provides an enterprise-ready, robust, and transparent platform fulfilling all requirements of the IGNOU MCA MCSP-232 curriculum.

For any additional technical questions or project demonstration assistance, please refer to the project repository documentation or consult with guide **Anchitha G Babu**.
