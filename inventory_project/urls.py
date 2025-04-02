from django.urls import path, include
from rest_framework.routers import DefaultRouter
from inventory.views import (
    CategoryViewSet, UnitOfMeasureViewSet, ItemViewSet,
    ItemTransactionViewSet, SupplierViewSet
)
from users.views import DepartmentViewSet, UserViewSet
from store_requisition.views import (
    StoreRequisitionViewSet, SRItemViewSet,
    StoreIssueViewSet, SIVItemViewSet
)
from purchase_requisition.views import PurchaseRequisitionViewSet, PRItemViewSet
from goods_receiving.views import GoodsReceivingNoteViewSet, GRNItemViewSet

# Create a router and register our viewsets with it
router = DefaultRouter()

# Inventory routes
router.register(r'categories', CategoryViewSet)
router.register(r'units-of-measure', UnitOfMeasureViewSet)
router.register(r'items', ItemViewSet)
router.register(r'item-transactions', ItemTransactionViewSet)
router.register(r'suppliers', SupplierViewSet)

# User routes
router.register(r'departments', DepartmentViewSet)
router.register(r'users', UserViewSet)

# Store requisition routes
router.register(r'store-requisitions', StoreRequisitionViewSet)
router.register(r'sr-items', SRItemViewSet)
router.register(r'store-issues', StoreIssueViewSet)
router.register(r'siv-items', SIVItemViewSet)

# Purchase requisition routes
router.register(r'purchase-requisitions', PurchaseRequisitionViewSet)
router.register(r'pr-items', PRItemViewSet)

# Goods receiving routes
router.register(r'goods-receiving-notes', GoodsReceivingNoteViewSet)
router.register(r'grn-items', GRNItemViewSet)

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
]
