# User Manual - Inventory Management System

## Table of Contents
1. Introduction
2. Getting Started
3. Dashboard
4. Inventory Management
5. Store Requisitions
6. Store Issues
7. Purchase Requisitions
8. Goods Receiving
9. Reports
10. User Management
11. Troubleshooting

## 1. Introduction

The Inventory Management System is a comprehensive solution designed to digitize and streamline your organization's inventory management processes. This system replaces paper-based workflows with an efficient digital solution that handles:

- Inventory tracking and management
- Store requisitions and issues
- Purchase requisitions
- Goods receiving
- Reporting and analytics

This user manual provides detailed instructions on how to use all features of the system.

## 2. Getting Started

### System Requirements
- Modern web browser (Chrome, Firefox, Edge, or Safari)
- Internet connection
- User account provided by your system administrator

### Logging In
1. Open your web browser and navigate to the system URL provided by your administrator
2. Enter your username and password
3. Click the "Login" button

### Navigation
The main navigation menu is located at the top of the screen and provides access to all system modules:
- Dashboard
- Inventory
- Store Requisitions
- Store Issues
- Purchases
- Reports
- Admin (visible only to administrators)

## 3. Dashboard

The dashboard provides an overview of key inventory metrics and recent activities:

### Overview Cards
- Total Items: Total number of items in inventory
- Low Stock Items: Number of items below minimum stock level
- Pending Requisitions: Number of requisitions awaiting approval
- Inventory Value: Total value of current inventory

### Low Stock Alerts
This section displays items that have fallen below their minimum stock levels. You can:
- View all low stock items by clicking "View All"
- Create a purchase requisition directly by clicking "Create PR" next to an item

### Recent Activities
The dashboard shows recent store requisitions and goods receiving notes, allowing you to:
- View details of recent transactions
- Monitor pending approvals
- Track recent inventory movements

## 4. Inventory Management

### Viewing Inventory Items
1. Click "Inventory" in the main menu, then select "Items"
2. Use filters to narrow down the list:
   - Category
   - Stock Level (All/Low Stock)
   - Search by code or description
3. Click on an item to view its details

### Item Details
The item detail page shows:
- Basic information (code, description, category)
- Current stock level and minimum stock level
- Current price
- Transaction history

### Adding a New Item
1. From the items list, click "Add New Item"
2. Fill in the required fields:
   - Item Code (unique identifier)
   - Description
   - Category (select from dropdown)
   - Unit of Measure
   - Minimum Stock Level
   - Current Price (if known)
3. Click "Save" to create the item

### Editing an Item
1. From the items list, find the item and click the edit icon
2. Update the necessary fields
3. Click "Save" to update the item

## 5. Store Requisitions

### Creating a Store Requisition
1. Click "Store Requisitions" in the main menu, then select "Create Requisition"
2. Fill in the requisition details:
   - Department (defaults to your department)
   - Delivery Date
3. Add items to the requisition:
   - Click "Add Item" to add a row
   - Select an item from the dropdown
   - Enter the requested quantity
   - Add more items as needed
4. Click "Submit Requisition" to create the requisition

### Viewing Requisitions
1. Click "Store Requisitions" in the main menu, then select "All Requisitions"
2. Use filters to narrow down the list:
   - Department
   - Status
   - Date range
3. Click on a requisition to view its details

### Checking a Requisition (for Controllers)
1. From the requisition details page, click "Check Requisition"
2. Review the requested items
3. Enter the checked quantity for each item
4. Click "Submit" to mark the requisition as checked

### Approving a Requisition (for Managers)
1. From the requisition details page, click "Approve Requisition"
2. Review the requested/checked items
3. Enter the approved quantity for each item
4. Click "Submit" to approve the requisition

### Rejecting a Requisition (for Managers)
1. From the requisition details page, click "Reject Requisition"
2. Enter a reason for rejection (optional)
3. Click "Submit" to reject the requisition

## 6. Store Issues

### Creating a Store Issue
1. Click "Store Issues" in the main menu, then select "Create Issue"
2. Select an approved requisition from the dropdown
3. The items will be populated automatically from the requisition
4. Adjust quantities if necessary
5. Enter the name of the person receiving the items
6. Click "Save Goods Issue Voucher" to create the issue

### Viewing Store Issues
1. Click "Store Issues" in the main menu, then select "All Issues"
2. Use filters to narrow down the list
3. Click on an issue to view its details

### Printing a Store Issue Voucher
1. From the issue details page, click "Print"
2. A printable version of the voucher will open
3. Use your browser's print function to print the voucher

## 7. Purchase Requisitions

### Creating a Purchase Requisition
1. Click "Purchases" in the main menu, then select "Create PR"
2. Fill in the requisition details:
   - Date (defaults to today)
   - Notes (optional)
3. Add items to the requisition:
   - Click "Add Item" to add a row
   - Select an item from the dropdown
   - Enter the quantity
   - Enter the estimated unit price (if known)
   - Add more items as needed
4. Click "Submit for Approval" to create the requisition

### Viewing Purchase Requisitions
1. Click "Purchases" in the main menu, then select "Purchase Requisitions"
2. Use filters to narrow down the list
3. Click on a requisition to view its details

### Approving a Purchase Requisition (for Managers)
1. From the requisition details page, click "Approve"
2. Review the requested items
3. Adjust quantities and prices if necessary
4. Click "Submit" to approve the requisition

### Rejecting a Purchase Requisition (for Managers)
1. From the requisition details page, click "Reject"
2. Enter a reason for rejection
3. Click "Submit" to reject the requisition

### Marking as Ordered (for Procurement)
1. From the approved requisition details page, click "Mark as Ordered"
2. Confirm the action
3. The requisition status will change to "Ordered"

## 8. Goods Receiving

### Creating a Goods Receiving Note
1. Click "Purchases" in the main menu, then select "Create GRN"
2. Fill in the GRN details:
   - Date (defaults to today)
   - Supplier (select from dropdown)
   - Invoice Number
   - Purchase Requisition (optional, select from dropdown)
   - Upload Receipt/Invoice (optional)
3. If a PR is selected, items will be populated automatically
4. Otherwise, add items manually:
   - Click "Add Item" to add a row
   - Select an item from the dropdown
   - Enter the quantity received
   - Enter the unit price
   - Add more items as needed
5. Click "Save Goods Receiving Note" to create the GRN

### Viewing Goods Receiving Notes
1. Click "Purchases" in the main menu, then select "Goods Receiving"
2. Use filters to narrow down the list
3. Click on a GRN to view its details

### Printing a Goods Receiving Note
1. From the GRN details page, click "Print"
2. A printable version of the note will open
3. Use your browser's print function to print the note

## 9. Reports

### Inventory Status Report
1. Click "Reports" in the main menu, then select "Inventory Status"
2. Use filters to customize the report:
   - Category
   - Stock Level (All/Low Stock)
   - Search by code or description
3. View the report on screen or export to CSV by clicking "Export to CSV"

### Transactions Report
1. Click "Reports" in the main menu, then select "Transactions"
2. Use filters to customize the report:
   - Item
   - Transaction Type
   - Date Range
3. View the report on screen or export to CSV

### Requisitions Report
1. Click "Reports" in the main menu, then select "Requisitions"
2. Use filters to customize the report:
   - Department
   - Status
   - Date Range
3. View the report on screen or export to CSV

### Purchases Report
1. Click "Reports" in the main menu, then select "Purchases"
2. Use filters to customize the report:
   - Status
   - Date Range
3. View the report on screen or export to CSV

## 10. User Management (for Administrators)

### Viewing Users
1. Click "Admin" in the main menu, then select "Users"
2. Use filters to narrow down the list:
   - Role
   - Department
   - Active Status
3. Click on a user to view their details

### Adding a New User
1. From the users list, click "Add New User"
2. Fill in the required fields:
   - Username
   - Email
   - First Name
   - Last Name
   - Role
   - Department
   - Password
3. Click "Save" to create the user

### Editing a User
1. From the users list, find the user and click the edit icon
2. Update the necessary fields
3. Click "Save" to update the user

### Deactivating a User
1. From the users list, find the user and click the "Deactivate" button
2. Confirm the action
3. The user will be deactivated and unable to log in

### Managing Departments
1. Click "Admin" in the main menu, then select "Departments"
2. View, add, edit, or delete departments as needed

## 11. Troubleshooting

### Common Issues

**Issue**: Unable to log in
**Solution**: 
- Verify that you're using the correct username and password
- Check if your account is active (contact administrator)
- Clear browser cache and cookies

**Issue**: Item not showing in dropdown
**Solution**:
- Check if the item exists in the inventory
- Verify that you have permission to access the item
- Try searching by item code or description

**Issue**: Cannot approve a requisition
**Solution**:
- Verify that you have the appropriate role (Manager or Admin)
- Check if the requisition is in the correct status (Pending or Checked)

**Issue**: Inventory not updating after transaction
**Solution**:
- Refresh the page
- Check if the transaction was completed successfully
- Contact your system administrator if the issue persists

### Getting Help
If you encounter any issues not covered in this manual, please contact your system administrator or the IT support team.
