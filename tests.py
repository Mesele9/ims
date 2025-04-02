import unittest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from inventory.models import Category, UnitOfMeasure, Item, Supplier
from users.models import Department
from store_requisition.models import StoreRequisition, SRItem
from purchase_requisition.models import PurchaseRequisition, PRItem
from goods_receiving.models import GoodsReceivingNote, GRNItem

User = get_user_model()

class InventoryModelTests(TestCase):
    """Test cases for inventory models"""
    
    def setUp(self):
        # Create test data
        self.category = Category.objects.create(
            name="Test Category",
            description="Test category description"
        )
        
        self.uom = UnitOfMeasure.objects.create(
            name="Each",
            abbreviation="EA"
        )
        
        self.item = Item.objects.create(
            code="ITEM001",
            description="Test Item",
            category=self.category,
            unit_of_measure=self.uom,
            min_stock_level=10,
            current_balance=20,
            current_price=15.00
        )
        
        self.supplier = Supplier.objects.create(
            name="Test Supplier",
            contact_person="John Doe",
            email="john@example.com",
            phone="1234567890",
            address="123 Test St"
        )
    
    def test_category_creation(self):
        """Test category model creation"""
        self.assertEqual(self.category.name, "Test Category")
        self.assertEqual(self.category.description, "Test category description")
        self.assertTrue(isinstance(self.category, Category))
        self.assertEqual(str(self.category), "Test Category")
    
    def test_uom_creation(self):
        """Test unit of measure model creation"""
        self.assertEqual(self.uom.name, "Each")
        self.assertEqual(self.uom.abbreviation, "EA")
        self.assertTrue(isinstance(self.uom, UnitOfMeasure))
        self.assertEqual(str(self.uom), "Each (EA)")
    
    def test_item_creation(self):
        """Test item model creation"""
        self.assertEqual(self.item.code, "ITEM001")
        self.assertEqual(self.item.description, "Test Item")
        self.assertEqual(self.item.category, self.category)
        self.assertEqual(self.item.unit_of_measure, self.uom)
        self.assertEqual(self.item.min_stock_level, 10)
        self.assertEqual(self.item.current_balance, 20)
        self.assertEqual(self.item.current_price, 15.00)
        self.assertTrue(isinstance(self.item, Item))
        self.assertEqual(str(self.item), "ITEM001 - Test Item")
    
    def test_supplier_creation(self):
        """Test supplier model creation"""
        self.assertEqual(self.supplier.name, "Test Supplier")
        self.assertEqual(self.supplier.contact_person, "John Doe")
        self.assertEqual(self.supplier.email, "john@example.com")
        self.assertEqual(self.supplier.phone, "1234567890")
        self.assertEqual(self.supplier.address, "123 Test St")
        self.assertTrue(isinstance(self.supplier, Supplier))
        self.assertEqual(str(self.supplier), "Test Supplier")
    
    def test_item_is_low_stock(self):
        """Test item low stock property"""
        # Current setup: min_stock_level=10, current_balance=20
        self.assertFalse(self.item.is_low_stock)
        
        # Update to low stock
        self.item.current_balance = 5
        self.item.save()
        self.assertTrue(self.item.is_low_stock)
        
        # Update to equal min stock
        self.item.current_balance = 10
        self.item.save()
        self.assertTrue(self.item.is_low_stock)
        
        # Update to above min stock
        self.item.current_balance = 11
        self.item.save()
        self.assertFalse(self.item.is_low_stock)


class UserModelTests(TestCase):
    """Test cases for user models"""
    
    def setUp(self):
        # Create test data
        self.department = Department.objects.create(
            name="IT Department",
            description="Information Technology Department"
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
        
        self.staff_user = User.objects.create_user(
            username="staff",
            email="staff@example.com",
            password="password123",
            first_name="Staff",
            last_name="User",
            role="staff",
            department=self.department
        )
    
    def test_department_creation(self):
        """Test department model creation"""
        self.assertEqual(self.department.name, "IT Department")
        self.assertEqual(self.department.description, "Information Technology Department")
        self.assertTrue(isinstance(self.department, Department))
        self.assertEqual(str(self.department), "IT Department")
    
    def test_user_creation(self):
        """Test user model creation"""
        self.assertEqual(self.admin_user.username, "admin")
        self.assertEqual(self.admin_user.email, "admin@example.com")
        self.assertEqual(self.admin_user.first_name, "Admin")
        self.assertEqual(self.admin_user.last_name, "User")
        self.assertEqual(self.admin_user.role, "admin")
        self.assertEqual(self.admin_user.department, self.department)
        self.assertTrue(self.admin_user.is_staff)
        self.assertTrue(isinstance(self.admin_user, User))
        
        self.assertEqual(self.staff_user.username, "staff")
        self.assertEqual(self.staff_user.role, "staff")
        self.assertFalse(self.staff_user.is_staff)
    
    def test_get_full_name(self):
        """Test user get_full_name method"""
        self.assertEqual(self.admin_user.get_full_name(), "Admin User")
        self.assertEqual(self.staff_user.get_full_name(), "Staff User")


class StoreRequisitionModelTests(TestCase):
    """Test cases for store requisition models"""
    
    def setUp(self):
        # Create test data
        self.department = Department.objects.create(
            name="IT Department",
            description="Information Technology Department"
        )
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            first_name="Test",
            last_name="User",
            role="staff",
            department=self.department
        )
        
        self.category = Category.objects.create(name="Test Category")
        self.uom = UnitOfMeasure.objects.create(name="Each", abbreviation="EA")
        
        self.item1 = Item.objects.create(
            code="ITEM001",
            description="Test Item 1",
            category=self.category,
            unit_of_measure=self.uom,
            current_balance=20
        )
        
        self.item2 = Item.objects.create(
            code="ITEM002",
            description="Test Item 2",
            category=self.category,
            unit_of_measure=self.uom,
            current_balance=30
        )
        
        # Create store requisition
        self.requisition = StoreRequisition.objects.create(
            department=self.department,
            requested_by=self.user,
            status="pending"
        )
        
        # Create SR items
        self.sr_item1 = SRItem.objects.create(
            sr=self.requisition,
            item=self.item1,
            requested_qty=5
        )
        
        self.sr_item2 = SRItem.objects.create(
            sr=self.requisition,
            item=self.item2,
            requested_qty=10
        )
    
    def test_requisition_creation(self):
        """Test store requisition model creation"""
        self.assertEqual(self.requisition.department, self.department)
        self.assertEqual(self.requisition.requested_by, self.user)
        self.assertEqual(self.requisition.status, "pending")
        self.assertTrue(isinstance(self.requisition, StoreRequisition))
        self.assertTrue(self.requisition.requisition_no.startswith("SR"))
    
    def test_sr_item_creation(self):
        """Test SR item model creation"""
        self.assertEqual(self.sr_item1.sr, self.requisition)
        self.assertEqual(self.sr_item1.item, self.item1)
        self.assertEqual(self.sr_item1.requested_qty, 5)
        self.assertIsNone(self.sr_item1.checked_qty)
        self.assertIsNone(self.sr_item1.approved_qty)
        self.assertTrue(isinstance(self.sr_item1, SRItem))
    
    def test_requisition_items_relationship(self):
        """Test relationship between requisition and items"""
        self.assertEqual(self.requisition.items.count(), 2)
        self.assertIn(self.sr_item1, self.requisition.items.all())
        self.assertIn(self.sr_item2, self.requisition.items.all())


class PurchaseRequisitionModelTests(TestCase):
    """Test cases for purchase requisition models"""
    
    def setUp(self):
        # Create test data
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        self.category = Category.objects.create(name="Test Category")
        self.uom = UnitOfMeasure.objects.create(name="Each", abbreviation="EA")
        
        self.item1 = Item.objects.create(
            code="ITEM001",
            description="Test Item 1",
            category=self.category,
            unit_of_measure=self.uom
        )
        
        self.item2 = Item.objects.create(
            code="ITEM002",
            description="Test Item 2",
            category=self.category,
            unit_of_measure=self.uom
        )
        
        # Create purchase requisition
        self.requisition = PurchaseRequisition.objects.create(
            requested_by=self.user,
            status="pending_approval"
        )
        
        # Create PR items
        self.pr_item1 = PRItem.objects.create(
            pr=self.requisition,
            item=self.item1,
            quantity=5,
            unit_price=10.00,
            total_price=50.00
        )
        
        self.pr_item2 = PRItem.objects.create(
            pr=self.requisition,
            item=self.item2,
            quantity=10,
            unit_price=15.00,
            total_price=150.00
        )
    
    def test_requisition_creation(self):
        """Test purchase requisition model creation"""
        self.assertEqual(self.requisition.requested_by, self.user)
        self.assertEqual(self.requisition.status, "pending_approval")
        self.assertTrue(isinstance(self.requisition, PurchaseRequisition))
        self.assertTrue(self.requisition.pr_no.startswith("PR"))
    
    def test_pr_item_creation(self):
        """Test PR item model creation"""
        self.assertEqual(self.pr_item1.pr, self.requisition)
        self.assertEqual(self.pr_item1.item, self.item1)
        self.assertEqual(self.pr_item1.quantity, 5)
        self.assertEqual(self.pr_item1.unit_price, 10.00)
        self.assertEqual(self.pr_item1.total_price, 50.00)
        self.assertTrue(isinstance(self.pr_item1, PRItem))
    
    def test_requisition_items_relationship(self):
        """Test relationship between requisition and items"""
        self.assertEqual(self.requisition.items.count(), 2)
        self.assertIn(self.pr_item1, self.requisition.items.all())
        self.assertIn(self.pr_item2, self.requisition.items.all())


class GoodsReceivingModelTests(TestCase):
    """Test cases for goods receiving models"""
    
    def setUp(self):
        # Create test data
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        self.supplier = Supplier.objects.create(
            name="Test Supplier",
            contact_person="John Doe",
            email="john@example.com"
        )
        
        self.category = Category.objects.create(name="Test Category")
        self.uom = UnitOfMeasure.objects.create(name="Each", abbreviation="EA")
        
        self.item1 = Item.objects.create(
            code="ITEM001",
            description="Test Item 1",
            category=self.category,
            unit_of_measure=self.uom,
            current_balance=0,
            current_price=0
        )
        
        self.item2 = Item.objects.create(
            code="ITEM002",
            description="Test Item 2",
            category=self.category,
            unit_of_measure=self.uom,
            current_balance=0,
            current_price=0
        )
        
        # Create goods receiving note
        self.grn = GoodsReceivingNote.objects.create(
            supplier=self.supplier,
            received_by=self.user,
            invoice_no="INV12345"
        )
        
        # Create GRN items
        self.grn_item1 = GRNItem.objects.create(
            grn=self.grn,
            item=self.item1,
            quantity=5,
            unit_price=10.00,
            total_price=50.00
        )
        
        self.grn_item2 = GRNItem.objects.create(
            grn=self.grn,
            item=self.item2,
            quantity=10,
            unit_price=15.00,
            total_price=150.00
        )
    
    def test_grn_creation(self):
        """Test goods receiving note model creation"""
        self.assertEqual(self.grn.supplier, self.supplier)
        self.assertEqual(self.grn.received_by, self.user)
        self.assertEqual(self.grn.invoice_no, "INV12345")
        self.assertTrue(isinstance(self.grn, GoodsReceivingNote))
        self.assertTrue(self.grn.grn_no.startswith("GRN"))
    
    def test_grn_item_creation(self):
        """Test GRN item model creation"""
        self.assertEqual(self.grn_item1.grn, self.grn)
        self.assertEqual(self.grn_item1.item, self.item1)
        self.assertEqual(self.grn_item1.quantity, 5)
        self.assertEqual(self.grn_item1.unit_price, 10.00)
        self.assertEqual(self.grn_item1.total_price, 50.00)
        self.assertTrue(isinstance(self.grn_item1, GRNItem))
    
    def test_grn_items_relationship(self):
        """Test relationship between GRN and items"""
        self.assertEqual(self.grn.items.count(), 2)
        self.assertIn(self.grn_item1, self.grn.items.all())
        self.assertIn(self.grn_item2, self.grn.items.all())
    
    def test_inventory_update_on_grn(self):
        """Test that inventory is updated when GRN is created"""
        # Refresh items from database
        self.item1.refresh_from_db()
        self.item2.refresh_from_db()
        
        # Check that inventory was updated
        self.assertEqual(self.item1.current_balance, 5)
        self.assertEqual(self.item1.current_price, 10.00)
        
        self.assertEqual(self.item2.current_balance, 10)
        self.assertEqual(self.item2.current_price, 15.00)


class AuthenticationTests(TestCase):
    """Test cases for authentication"""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        # Create client
        self.client = Client()
    
    def test_login(self):
        """Test user login"""
        # Test login with correct credentials
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
        
        # Test login with incorrect credentials
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)  # Stay on login page
    
    def test_logout(self):
        """Test user logout"""
        # Login first
        self.client.login(username='testuser', password='password123')
        
        # Test logout
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)  # Redirect after logout
    
    def test_protected_views(self):
        """Test that views are protected"""
        # Try to access dashboard without login
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Login
        self.client.login(username='testuser', password='password123')
        
        # Try to access dashboard with login
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)  # Access granted


if __name__ == '__main__':
    unittest.main()
