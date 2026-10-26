import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.db.base import Base
from backend.app.db.session import SessionLocal, engine
from backend.app.repositories.user_repo import UserRepository
from backend.app.schemas.item import ItemCreate
from backend.app.schemas.movement import IssueCreate, ReceiptCreate
from backend.app.schemas.purchase_request import PurchaseRequestCreate, PurchaseRequestLineCreate
from backend.app.schemas.supplier import SupplierCreate
from backend.app.schemas.user import UserCreate, UserRole
from backend.app.services.inventory_service import InventoryService
from backend.app.services.procurement_service import ProcurementService
from backend.app.services.stock_engine import StockEngine


def seed_demo_data():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        user_repo = UserRepository(db)
        inv_service = InventoryService(db)
        stock_engine = StockEngine(db)
        proc_service = ProcurementService(db)

        # 1. Users
        admin = user_repo.get_by_email("admin@labstock.edu")
        if not admin:
            admin = user_repo.create(
                UserCreate(
                    email="admin@labstock.edu",
                    full_name="Dr. Elena Vance (Lead Admin)",
                    password="AdminPassword123#",
                    role=UserRole.ADMINISTRATOR,
                    is_active=True,
                )
            )
            print("Created Admin: admin@labstock.edu")

        manager = user_repo.get_by_email("manager@labstock.edu")
        if not manager:
            manager = user_repo.create(
                UserCreate(
                    email="manager@labstock.edu",
                    full_name="Rajesh Patel (Lab Technician)",
                    password="ManagerPassword123#",
                    role=UserRole.INVENTORY_MANAGER,
                    is_active=True,
                )
            )
            print("Created Manager: manager@labstock.edu")

        viewer = user_repo.get_by_email("viewer@labstock.edu")
        if not viewer:
            viewer = user_repo.create(
                UserCreate(
                    email="viewer@labstock.edu",
                    full_name="Maya Lin (Research Student)",
                    password="ViewerPassword123#",
                    role=UserRole.VIEWER,
                    is_active=True,
                )
            )
            print("Created Viewer: viewer@labstock.edu")

        # 2. Suppliers
        from backend.app.repositories.supplier_repo import SupplierRepository

        sup_repo = SupplierRepository(db)

        sup1 = sup_repo.get_by_name("RoboRobotics Components Ltd")
        if not sup1:
            sup1 = sup_repo.create(
                SupplierCreate(
                    name="RoboRobotics Components Ltd",
                    contact_person="Anita Sharma",
                    email="orders@roborobotics.com",
                    phone="+91 98765 43210",
                    address="Tech Park Phase 2, Bangalore, India",
                    notes="Preferred supplier for motor drivers, microcontrollers, and sensors.",
                    is_active=True,
                )
            )
            print("Created Supplier: RoboRobotics Components Ltd")

        sup2 = sup_repo.get_by_name("Semiconductor Supply Hub")
        if not sup2:
            sup2 = sup_repo.create(
                SupplierCreate(
                    name="Semiconductor Supply Hub",
                    contact_person="David Miller",
                    email="sales@semisupplyhub.com",
                    phone="+1 555 019 2831",
                    address="Silicon Valley, CA, USA",
                    notes="Passives, ICs, and voltage regulators.",
                    is_active=True,
                )
            )
            print("Created Supplier: Semiconductor Supply Hub")

        # 3. Items matching the design screens
        demo_items = [
            {
                "sku": "EL-MTR-042",
                "name": "DC Motor Driver L298N",
                "description": "Dual H-bridge motor driver module with heat sink and terminal blocks.",
                "category": "Electronics",
                "unit": "pcs",
                "storage_location": "Shelf B-04",
                "min_stock_threshold": 15.0,
                "target_stock": 40.0,
                "initial_stock": 2.0,  # Will show as LOW STOCK (2 <= 15)
                "preferred_supplier_id": sup1.id,
                "manufacturer_model": "L298N Dual H-Bridge",
            },
            {
                "sku": "SN-ULT-109",
                "name": "Ultrasonic Sensor HC-SR04",
                "description": "4-pin ultrasonic distance measuring transducer module 2cm-400cm.",
                "category": "Sensors",
                "unit": "pcs",
                "storage_location": "Shelf A-12",
                "min_stock_threshold": 20.0,
                "target_stock": 50.0,
                "initial_stock": 0.0,  # Will show as OUT OF STOCK
                "preferred_supplier_id": sup1.id,
                "manufacturer_model": "HC-SR04",
            },
            {
                "sku": "MC-ESP-032",
                "name": "ESP32-WROOM-32D Development Board",
                "description": "Dual-core 240MHz Wi-Fi + BLE microcontroller dev board with CP2102.",
                "category": "Microcontrollers",
                "unit": "pcs",
                "storage_location": "Cabinet C, Drawer 2",
                "min_stock_threshold": 10.0,
                "target_stock": 30.0,
                "initial_stock": 25.0,  # IN STOCK
                "preferred_supplier_id": sup1.id,
                "manufacturer_model": "ESP32-WROOM-32D",
            },
            {
                "sku": "SBC-RPI-004",
                "name": "Raspberry Pi 4 Model B (4GB RAM)",
                "description": "Single board computer with quad-core Cortex-A72 and dual micro-HDMI.",
                "category": "Single Board Computers",
                "unit": "pcs",
                "storage_location": "Cabinet C, Shelf 1",
                "min_stock_threshold": 5.0,
                "target_stock": 15.0,
                "initial_stock": 8.0,  # IN STOCK
                "preferred_supplier_id": sup1.id,
                "manufacturer_model": "RPi-4B-4GB",
            },
            {
                "sku": "IC-VR-7805",
                "name": "Linear Voltage Regulator LM7805 5V 1.5A",
                "description": "TO-220 positive fixed voltage regulator.",
                "category": "Semiconductors",
                "unit": "pcs",
                "storage_location": "Bin 14-A",
                "min_stock_threshold": 50.0,
                "target_stock": 150.0,
                "initial_stock": 120.0,  # IN STOCK
                "preferred_supplier_id": sup2.id,
                "manufacturer_model": "LM7805T",
            },
            {
                "sku": "PAS-CAP-104",
                "name": "Ceramic Capacitor 100nF (0.1uF) 50V",
                "description": "Radial lead multilayer ceramic capacitor for decoupling.",
                "category": "Passive Components",
                "unit": "pcs",
                "storage_location": "Bin 08-C",
                "min_stock_threshold": 100.0,
                "target_stock": 500.0,
                "initial_stock": 85.0,  # LOW STOCK (85 <= 100)
                "preferred_supplier_id": sup2.id,
                "manufacturer_model": "Kemet C315C104M5U5TA",
            },
        ]

        created_item_map = {}
        for d in demo_items:
            existing = inv_service.item_repo.get_by_sku(d["sku"])
            if not existing:
                init_qty = d.pop("initial_stock")
                it = inv_service.create_item(ItemCreate(**d), actor_id=admin.id)
                if init_qty > 0:
                    stock_engine.receive_stock(
                        ReceiptCreate(
                            item_id=it.id,
                            quantity=init_qty,
                            reference_type="opening_receipt",
                            reason="Initial physical count",
                        ),
                        actor_id=admin.id,
                    )
                created_item_map[it.sku] = it
                print(f"Created Item: {it.sku} - {it.name}")
            else:
                created_item_map[existing.sku] = existing

        # 4. Sample Issue to demonstrate ledger and consumption
        esp32 = created_item_map.get("MC-ESP-032")
        if esp32:
            try:
                stock_engine.issue_stock(
                    IssueCreate(
                        item_id=esp32.id,
                        quantity=3.0,
                        recipient_project="Robotics Club — Autonomous Drone Team",
                        reference_type="student_project",
                        reason="Hardware prototyping for drone navigation",
                    ),
                    actor_id=manager.id,
                )
                print("Logged demo issue of 3 ESP32 boards to Autonomous Drone Team.")
            except Exception as e:
                print(f"Demo issue note: {e}")

        # 5. Sample Purchase Request for Ultrasonic Sensors
        hc_sr04 = created_item_map.get("SN-ULT-109")
        if hc_sr04:
            pr = proc_service.create_request(
                requester_id=manager.id,
                pr_in=PurchaseRequestCreate(
                    supplier_id=sup1.id,
                    notes="Urgent replenishment for upcoming Mechatronics lab courses.",
                    lines=[
                        PurchaseRequestLineCreate(
                            item_id=hc_sr04.id,
                            requested_quantity=50.0,
                            unit_cost=1.20,
                            notes="Required before term start",
                        )
                    ],
                ),
            )
            proc_service.submit_request(pr.id, actor_id=manager.id)
            print(f"Created & Submitted Demo Purchase Request: {pr.request_number}")

        print("\nDemo seed completed successfully!")
        print("Login credentials:")
        print("  Administrator: admin@labstock.edu / AdminPassword123#")
        print("  Manager:       manager@labstock.edu / ManagerPassword123#")
        print("  Viewer:        viewer@labstock.edu / ViewerPassword123#")

    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
