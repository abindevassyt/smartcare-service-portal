# SmartCare Service Portal (MCSP-232)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://www.djangoproject.com/)
[![Database](https://img.shields.io/badge/Database-MySQL%20%2F%20SQLite-orange.svg)](https://www.mysql.com/)
[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen.svg)]()

> **Master of Computer Applications (MCA) Project**  
> **Course Code**: MCSP-232 | **IGNOU 2026**  
> **Student**: Abin Devassy Tharayil (*Enrolment No: 2550779223*)  
> **Project Guide**: Anchitha G Babu  

---

## Executive Summary

The **SmartCare Service Portal** is an enterprise-grade after-sales service management and warranty lifecycle platform designed for consumer electronics and home appliance manufacturers. The system orchestrates end-to-end service ticket workflows across three role-based portals: **Administrator**, **Field Technician**, and **Consumer**.

### Key Capabilities
- **Appliance Activation Gate**: Newly registered appliances require proof validation and technician verification before service bookings can be opened.
- **Automated Warranty Engine**: Dynamically calculates remaining warranty days and coverage validity (`In Warranty` vs `Out of Warranty`).
- **Estimate Approval Workflow**: Consumers receive transparent repair estimates for out-of-warranty appliances with one-click **Accept Estimate** or **Cancel Request** actions.
- **Technician Diagnostics Workbench**: Unified multi-panel workspace to log technical defect classifications, symptoms, and step-by-step audit updates.
- **Atomic Spare Parts Inventory**: Real-time inventory deduction wrapped in database transactions preventing over-allocation or stock corruption.
- **Automated Billing Engine**: Implements strict business rules:
  - **Rule 1 (In Warranty)**: Rs. 0.00 charge; irreparable appliances escalate for Warranty Replacement.
  - **Rule 2 (Out of Warranty & Irreparable)**: Rs. 0.00 charge (no-charge diagnostic policy).
  - **Rule 3 (Out of Warranty & Repaired)**: Total = Spare Parts Cost + Labor Service Fee.
- **Printable Tax Invoices**: Standardized formal service invoice with service center letterhead, GSTIN, itemized parts, warranty waiver banner, and high-fidelity `@media print` CSS.
- **Admin Management Reports Hub**: 4 dedicated analytical modules with filter controls and one-click real-time CSV streaming.

---

## Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11, Django 5.2 |
| **Database** | MySQL (Database: `smartcare_db` via PyMySQL) with automatic fallback to SQLite |
| **Frontend** | HTML5, CSS3 (Deep Navy & Electric Cyan Design System), Vanilla JavaScript |
| **Security** | Custom Session Authentication, PBKDF2 Password Hashing, Role Decorators (`@admin_required`, `@tech_required`, `@consumer_required`), Ownership Verification |
| **Testing** | Django Automated Test Suite (17 unit tests, 100% pass rate) |

---

## Database Architecture (18 Relational Tables)

- **`accounts` App**:
  - `State`, `District`: Hierarchical geographic regions.
  - `serv_center`: Authorized service centers.
  - `Consumer_reg`: Customer profiles and contact details.
  - `Technicians`: Field technician master profiles.
  - `accounts_authuser`: Custom authentication credentials and RBAC roles.
- **`products` App**:
  - `Product_cat`: Product classifications (TV, Refrigerator, Washer, etc.).
  - `Product`: Master catalog with serial number format and image upload.
  - `Spare_parts`: Component inventory tracking unit prices and live stock quantities.
- **`services` App**:
  - `Cons_product_reg`: Customer appliance registrations with warranty metadata and activation gate.
  - `Work_status`: Lifecycle status definitions.
  - `Work_order`: Core service tickets and assignments.
  - `Activity_dtls`: Chronological audit trail of ticket updates.
  - `defects_symptom`: Technical defect diagnostic records.
  - `Service_parts`, `Service_parts_dtls`: Allocated replacement parts.
  - `Service_invoice`: Generated billing records.
  - `Complaints`: Customer inquiries and resolution replies.

---

## Quick Start & Setup Guide

### 1. Prerequisites
- Python 3.11 or higher
- Git
- MySQL Server (Optional — SQLite fallback works automatically out of the box)

### 2. Clone the Repository
```bash
git clone https://github.com/abindevassyt/smartcare-service-portal.git
cd smartcare-service-portal
```

### 3. Set Up Virtual Environment & Dependencies
```bash
# Create and activate virtual environment
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 4. Database Setup & Migrations
```bash
# Apply migrations for all 18 tables
python manage.py migrate

# Seed baseline master data, admin, technician, consumer, and sample order
python manage.py seed_initial_data
```

### 5. Run Development Server
```bash
python manage.py runserver
```

Open your browser at `http://127.0.0.1:8000/`.

---

## Pre-Configured Test Credentials

| Role | Username / Email | Password | Access Capabilities |
|---|---|---|---|
| **Administrator** | `admin` | `admin123` | Master Data CRUD, Dispatch, Reports Hub, Support |
| **Technician** | `rahul.tech` *(or `rahul.tech@smartcare.com`)* | `password123` | Activation Queues, Workbench, Billing Engine |
| **Consumer** | `consumer` *(or `consumer@smartcare.com`)* | `password123` | Appliance Registration, Booking, Timeline, Invoices |

*(You can also register new consumer accounts directly via `/register/`)*

---

## Automated Test Verification

Run the complete test suite covering all 8 development stages:
```bash
python manage.py test
```
All 17 automated tests verify authentication, activation gates, estimate approval, diagnostics, atomic inventory deduction, billing engine rules, printable invoices, and CSV reports.

---

## Documentation

- Detailed operations guide: [`USER_MANUAL.md`](USER_MANUAL.md)

---

## Author & Acknowledgements

- **Developer**: Abin Devassy Tharayil (Enrolment No: 2550779223)
- **Project Guide**: Anchitha G Babu
- **Institution**: Indira Gandhi National Open University (IGNOU)