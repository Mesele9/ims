import unittest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction

from inventory.models import Category, UnitOfMeasure, Item, Supplier, ItemTransaction
from users.models import Department
from store_requisition.models import StoreRequisition, SRItem, StoreIssue, SIVItem
from purchase_requisition.models import PurchaseRequisition, PRItem
from goods_receiving.models import GoodsReceivingNote, GRNItem

User = get_user_model()

class IntegrationTests(TestCase):
    """Integration tests for the inventory management system"""
    
    def setUp(self):
        # Create test data
        self.department = Department.objects.create(
            name="Engineering",
            description="Engineering Department"
        )
        
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="password123",
            first_name="Admin",
            last_name="User",
            role="admin",
            department=self.department,
            is_staff=True
        )
        
        self.store_keeper = User.objects.create_user(
            username="storekeeper",
            email="store@example.com",
            password="password123",
            first_name="Store",
            last_name="Keeper",
            role="store_keeper",
            department=self.department
        )
        
        self.staff_user = User.objects.create_user(
            username="staff",
            email="staff@example.com",
            password="password123",
            first_name="Staff",
            last_name="User",
            role="staff",
            department=self.department
        )
        
        self.category = Category.objects.create(
            name="Office Supplies",
            description="Office supplies and stationery"
        )
        
        self.uom = UnitOfMeasure.objects.create(
            name="Each",
            abbreviation="EA"
        )
        
        self.item1 = Item.objects.create(
            code="PEN001",
            description="Ballpoint Pen",
            category=self.category,
            unit_of_measure=self.uom,
            min_stock_level=10,
            current_balance=50,
            current_price=1.50
        )
        
        self.item2 = Item.objects.create(
            code="NB001",
            description="Notebook",
            category=self.category,
            unit_of_measure=self.uom,
            min_stock_level=5,
            current_balance=20,
            current_price=3.75
        )
        
        self.supplier = Supplier.objects.create(
            name="Office Depot",
            contact_person="John Smith",
            email="john@officedepot.com",
            phone="1234567890",
            address="123 Supply St"
        )
        
        # Create client
        self.client = Client()
    
    def test_complete_workflow(self):
        """Test the complete workflow from requisition to issue"""
        # Login as staff user
        self.client.login(username='staff', password='password123')
        
        # 1. Create store requisition
        with transaction.atomic():
            requisition = StoreRequisition.objects.create(
                department=self.department,
                requested_by=self.staff_user,
                requested_date=timezone.now().date(),
                delivery_date=timezone.now().date() + timezone.timedelta(days=3),
                status="pending"
            )
            
            # Add items to requisition
            sr_item1 = SRItem.objects.create(
                sr=requisition,
                item=self.item1,
                requested_qty=5
            )
            
            sr_item2 = SRItem.objects.create(
                sr=requisition,
                item=self.item2,
                requested_qty=2
            )
        
        # Verify requisition was created
        self.assertTrue(requisition.requisition_no.startswith("SR"))
        self.assertEqual(requisition.status, "pending")
        self.assertEqual(requisition.items.count(), 2)
        
        # 2. Login as admin to approve requisition
        self.client.logout()
        self.client.login(username='admin', password='password123')
        
        # Approve requisition
        with transaction.atomic():
            requisition.checked_by = self.admin_user
            requisition.checked_date = timezone.now().date()
            requisition.approved_by = self.admin_user
            requisition.approved_date = timezone.now().date()
            requisition.status = "approved"
            requisition.save()
            
            # Update item quantities
            sr_item1.checked_qty = 5
            sr_item1.approved_qty = 5
            sr_item1.save()
            
            sr_item2.checked_qty = 2
            sr_item2.approved_qty = 2
            sr_item2.save()
        
        # Verify requisition was approved
        requisition.refresh_from_db()
        self.assertEqual(requisition.status, "approved")
        self.assertEqual(requisition.approved_by, self.admin_user)
        
        # 3. Login as store keeper to issue items
        self.client.logout()
        self.client.login(username='storekeeper', password='password123')
        
        # Create store issue
        initial_balance_item1 = self.item1.current_balance
        initial_balance_item2 = self.item2.current_balance
        
        with transaction.atomic():
            store_issue = StoreIssue.objects.create(
                sr=requisition,
                date=timezone.now().date(),
                prepared_by=self.store_keeper,
                checked_by=self.store_keeper,
                issued_by=self.store_keeper,
                received_by="Jane Doe"
            )
            
            # Add items to issue
            siv_item1 = SIVItem.objects.create(
                siv=store_issue,
                item=self.item1,
                quantity=5,
                unit_price=self.item1.current_price,
                total_price=5 * self.item1.current_price
            )
            
            siv_item2 = SIVItem.objects.create(
                siv=store_issue,
                item=self.item2,
                quantity=2,
                unit_price=self.item2.current_price,
                total_price=2 * self.item2.current_price
            )
        
        # Verify store issue was created
        self.assertTrue(store_issue.siv_no.startswith("SIV"))
        self.assertEqual(store_issue.items.count(), 2)
        
        # Verify requisition status was updated
        requisition.refresh_from_db()
        self.assertEqual(requisition.status, "issued")
        
        # Verify inventory was updated
        self.item1.refresh_from_db()
        self.item2.refresh_from_db()
        
        self.assertEqual(self.item1.current_balance, initial_balance_item1 - 5)
        self.assertEqual(self.item2.current_balance, initial_balance_item2 - 2)
        
        # Verify transactions were created
        item1_transactions = ItemTransaction.objects.filter(
            item=self.item1,
            transaction_type="issue",
            reference=store_issue.siv_no
        )
        self.assertEqual(item1_transactions.count(), 1)
        self.assertEqual(item1_transactions.first().quantity_out, 5)
        
        item2_transactions = ItemTransaction.objects.filter(
            item=self.item2,
            transaction_type="issue",
            reference=store_issue.siv_no
        )
        self.assertEqual(item2_transactions.count(), 1)
        self.assertEqual(item2_transactions.first().quantity_out, 2)
    
    def test_purchase_and_receiving_workflow(self):
        """Test the complete workflow from purchase requisition to goods receiving"""
        # Login as staff user
        self.client.login(username='staff', password='password123')
        
        # 1. Create purchase requisition
        with transaction.atomic():
            pr = PurchaseRequisition.objects.create(
                requested_by=self.staff_user,
                date=timezone.now().date(),
                status="pending_approval"
            )
            
            # Add items to requisition
            pr_item1 = PRItem.objects.create(
                pr=pr,
                item=self.item1,
                quantity=20,
                unit_price=1.25,
                total_price=20 * 1.25
            )
            
            pr_item2 = PRItem.objects.create(
                pr=pr,
                item=self.item2,
                quantity=10,
                unit_price=3.50,
                total_price=10 * 3.50
            )
        
        # Verify PR was created
        self.assertTrue(pr.pr_no.startswith("PR"))
        self.assertEqual(pr.status, "pending_approval")
        self.assertEqual(pr.items.count(), 2)
        
        # 2. Login as admin to approve PR
        self.client.logout()
        self.client.login(username='admin', password='password123')
        
        # Approve PR
        with transaction.atomic():
            pr.approved_by = self.admin_user
            pr.approved_date = timezone.now().date()
            pr.status = "approved"
            pr.save()
        
        # Mark as ordered
        with transaction.atomic():
            pr.status = "ordered"
            pr.save()
        
        # Verify PR was approved and ordered
        pr.refresh_from_db()
        self.assertEqual(pr.status, "ordered")
        self.assertEqual(pr.approved_by, self.admin_user)
        
        # 3. Create goods receiving note
        initial_balance_item1 = self.item1.current_balance
        initial_balance_item2 = self.item2.current_balance
        
        with transaction.atomic():
            grn = GoodsReceivingNote.objects.create(
                supplier=self.supplier,
                date=timezone.now().date(),
                received_by=self.store_keeper,
                checked_by=self.admin_user,
                invoice_no="INV12345",
                pr=pr
            )
            
            # Add items to GRN
            grn_item1 = GRNItem.objects.create(
                grn=grn,
                item=self.item1,
                quantity=20,
                unit_price=1.25,
                total_price=20 * 1.25
            )
            
            grn_item2 = GRNItem.objects.create(
                grn=grn,
                item=self.item2,
                quantity=10,
                unit_price=3.50,
                total_price=10 * 3.50
            )
        
        # Verify GRN was created
        self.assertTrue(grn.grn_no.startswith("GRN"))
        self.assertEqual(grn.items.count(), 2)
        
        # Verify PR status was updated
        pr.refresh_from_db()
        self.assertEqual(pr.status, "received")
        
        # Verify inventory was updated
        self.item1.refresh_from_db()
        self.item2.refresh_from_db()
        
        self.assertEqual(self.item1.current_balance, initial_balance_item1 + 20)
        self.assertEqual(self.item2.current_balance, initial_balance_item2 + 10)
        
        # Verify transactions were created
        item1_transactions = ItemTransaction.objects.filter(
            item=self.item1,
            transaction_type="receive",
            reference=grn.grn_no
        )
        self.assertEqual(item1_transactions.count(), 1)
        self.assertEqual(item1_transactions.first().quantity_in, 20)
        
        item2_transactions = ItemTransaction.objects.filter(
            item=self.item2,
            transaction_type="receive",
            reference=grn.grn_no
        )
        self.assertEqual(item2_transactions.count(), 1)
        self.assertEqual(item2_transactions.first().quantity_in, 10)
    
    def test_weighted_average_price_calculation(self):
        """Test that weighted average price is calculated correctly on receiving"""
        # Initial state
        self.item1.current_balance = 10
        self.item1.current_price = 2.00
        self.item1.save()
        
        # Create GRN with different price
        with transaction.atomic():
            grn = GoodsReceivingNote.objects.create(
                supplier=self.supplier,
                date=timezone.now().date(),
                received_by=self.store_keeper,
                checked_by=self.admin_user,
                invoice_no="INV12345"
            )
            
            # Add item to GRN with different price
            grn_item = GRNItem.objects.create(
                grn=grn,
                item=self.item1,
                quantity=5,
                unit_price=3.00,
                total_price=5 * 3.00
            )
        
        # Verify weighted average price was calculated correctly
        # (10 * 2.00 + 5 * 3.00) / (10 + 5) = (20 + 15) / 15 = 35 / 15 = 2.33
        self.item1.refresh_from_db()
        self.assertAlmostEqual(self.item1.current_price, 2.33, places=2)
        self.assertEqual(self.item1.current_balance, 15)


if __name__ == '__main__':
    unittest.main()
