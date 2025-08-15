
#!/usr/bin/env python3
"""
LuxDB Enterprise Edition Demo
============================

Professional demonstration of template-instance pattern
with boring, reliable enterprise naming conventions.

No magic, no spirits, just solid data management.
"""

import asyncio
from luxdb_enterprise import EnterpriseDB, DataTemplate, DataInstance, InstanceFactory

async def main():
    print("🏢 LuxDB Enterprise Edition - Professional Demo")
    print("=" * 60)
    
    # Initialize enterprise database
    db = EnterpriseDB(
        host="your-postgres-host.com",
        port=5432,
        user="admin",
        password="enterprise_password",
        database="luxdb_enterprise"
    )
    
    await db.initialize()
    
    # Create professional user template
    user_schema = {
        "properties": {
            "employee_id": {
                "py_type": "str",
                "required": True,
                "description": "Unique employee identifier"
            },
            "full_name": {
                "py_type": "str", 
                "required": True,
                "description": "Employee full name"
            },
            "department": {
                "py_type": "str",
                "default": "General",
                "description": "Employee department"
            },
            "salary": {
                "py_type": "float",
                "description": "Employee salary"
            },
            "active": {
                "py_type": "bool",
                "default": True,
                "description": "Employment status"
            }
        }
    }
    
    print("\n📋 Creating Employee Template...")
    employee_template = await db.create_template(user_schema, "employee_template")
    print(f"✅ Template created: {employee_template}")
    
    # Create instance factory
    factory = InstanceFactory(db)
    
    print("\n🏭 Creating Employee Instances...")
    
    # Create individual employee
    john_data = {
        "employee_id": "EMP001",
        "full_name": "John Smith", 
        "department": "Engineering",
        "salary": 75000.0,
        "active": True
    }
    
    john = await factory.create_instance(
        "employee_template", 
        john_data,
        "employee_john_smith"
    )
    print(f"✅ Created: {john}")
    
    # Create batch of employees
    employee_batch = [
        {
            "employee_id": "EMP002",
            "full_name": "Jane Doe",
            "department": "Marketing", 
            "salary": 65000.0
        },
        {
            "employee_id": "EMP003",
            "full_name": "Bob Wilson",
            "department": "Sales",
            "salary": 70000.0
        }
    ]
    
    batch_employees = await factory.create_batch_instances(
        "employee_template",
        employee_batch,
        "employee"
    )
    
    print(f"✅ Created {len(batch_employees)} employees in batch")
    
    # Template with processor
    print("\n⚙️ Creating Template with Business Logic...")
    
    calculator_schema = {
        "properties": {
            "value": {
                "py_type": "float",
                "required": True,
                "description": "Numeric value for calculations"
            }
        }
    }
    
    # Add business logic module
    calculator_schema["module_source"] = '''
def init(being_context=None):
    """Initialize calculator processor"""
    return {
        "ready": True,
        "calculator_type": "enterprise_grade",
        "precision": "high"
    }

def calculate_tax(value, rate=0.15, being_context=None):
    """Calculate tax for given value"""
    tax_amount = value * rate
    return {
        "original_value": value,
        "tax_rate": rate,
        "tax_amount": tax_amount,
        "final_value": value + tax_amount,
        "calculation_type": "enterprise_tax_calculation"
    }

def calculate_bonus(value, percentage=0.10, being_context=None):
    """Calculate bonus percentage"""
    bonus_amount = value * percentage
    return {
        "base_value": value,
        "bonus_percentage": percentage,
        "bonus_amount": bonus_amount,
        "total_value": value + bonus_amount
    }

async def execute(request=None, being_context=None):
    """Main processor router"""
    if not request:
        return {
            "available_processors": ["calculate_tax", "calculate_bonus"],
            "calculator_ready": True
        }
    
    action = request.get('action') if isinstance(request, dict) else str(request)
    
    if action == 'calculate_tax':
        value = request.get('value', being_context.get('data', {}).get('value', 0))
        rate = request.get('rate', 0.15)
        return calculate_tax(value, rate, being_context)
    elif action == 'calculate_bonus':
        value = request.get('value', being_context.get('data', {}).get('value', 0))
        percentage = request.get('percentage', 0.10)
        return calculate_bonus(value, percentage, being_context)
    else:
        return {
            "error": f"Unknown processor: {action}",
            "available_processors": ["calculate_tax", "calculate_bonus"]
        }
'''
    
    calc_template = await db.create_template(calculator_schema, "enterprise_calculator")
    print(f"✅ Business logic template created: {calc_template}")
    
    # Create calculator instance
    calc_instance = await factory.create_instance(
        "enterprise_calculator",
        {"value": 50000.0},
        "salary_calculator"
    )
    
    print(f"✅ Calculator instance: {calc_instance}")
    
    # Execute business logic
    print("\n💼 Executing Business Logic...")
    
    tax_result = await calc_instance.execute_processor(
        "calculate_tax",
        value=50000.0,
        rate=0.20
    )
    
    print("📊 Tax Calculation Result:")
    print(f"   Original: ${tax_result['result']['original_value']:,.2f}")
    print(f"   Tax: ${tax_result['result']['tax_amount']:,.2f}")
    print(f"   Final: ${tax_result['result']['final_value']:,.2f}")
    
    bonus_result = await calc_instance.execute_processor(
        "calculate_bonus", 
        value=50000.0,
        percentage=0.15
    )
    
    print("\n💰 Bonus Calculation Result:")
    print(f"   Base: ${bonus_result['result']['base_value']:,.2f}")
    print(f"   Bonus: ${bonus_result['result']['bonus_amount']:,.2f}")
    print(f"   Total: ${bonus_result['result']['total_value']:,.2f}")
    
    # System statistics
    print("\n📈 Enterprise System Statistics:")
    stats = db.get_system_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
        
    factory_stats = factory.get_creation_statistics()
    print(f"\n🏭 Factory Statistics:")
    print(f"   Total created: {factory_stats['total_created']}")
    print(f"   Templates used: {factory_stats['templates_used']}")
    
    print("\n✅ Enterprise demo completed successfully!")
    print("🏢 No magic involved - just professional data management.")

if __name__ == "__main__":
    asyncio.run(main())
