
#!/usr/bin/env python3
"""
Demo pokazujące użycie Being.get_or_create() dla różnych typów bytów
"""

import asyncio
from luxdb.models.soul import Soul
from luxdb.models.being import Being

async def demo_get_or_create():
    print("🧬 Demo Being.get_or_create()\n")
    
    # 1. Kernel Soul - jeden per aplikacja (unique_by="soul_hash")
    kernel_genotype = {
        "genesis": {"name": "kernel", "version": "1.0", "type": "singleton"},
        "attributes": {
            "status": {"py_type": "str", "default": "initializing"},
            "uptime": {"py_type": "int", "default": 0}
        },
        "functions": {
            "init": {
                "py_type": "function",
                "description": "Initialize kernel system"
            },
            "get_status": {
                "py_type": "function", 
                "description": "Get current kernel status"
            }
        },
        "module_source": '''
def init(being_context=None):
    """Initialize kernel"""
    print(f"Kernel initialized for {being_context.get('alias', 'unknown')}")
    return {"status": "initialized", "message": "Kernel ready"}
    
def get_status(being_context=None):
    """Get kernel status"""
    return {"status": "running", "uptime": 3600}
'''
    }
    
    # 2. Message Soul - każdy unikalny (zawsze create)
    message_genotype = {
        "genesis": {"name": "message", "version": "1.0", "type": "multi_instance"},
        "attributes": {
            "content": {"py_type": "str"},
            "author": {"py_type": "str"},
            "timestamp": {"py_type": "str"}
        },
        "functions": {
            "init": {
                "py_type": "function",
                "description": "Initialize message processing"
            }
        },
        "module_source": '''
def init(being_context=None):
    """Initialize message"""
    print(f"Message initialized: {being_context.get('alias', 'unknown')}")
    return {"processed": True, "ready": True}
'''
    }
    
    # Utwórz Soul
    kernel_soul = await Soul.create(kernel_genotype, "kernel")
    message_soul = await Soul.create(message_genotype, "message")
    
    print("1. 🔧 Kernel Being - singleton pattern")
    
    # Pierwsze wywołanie - utworzy nowy Kernel
    kernel1 = await Being.get_or_create(
        kernel_soul, 
        alias="system_kernel",
        attributes={"status": "booting"},
        unique_by="soul_hash"  # Jeden per soul_hash
    )
    print(f"   Pierwszy kernel: {kernel1.alias} ({kernel1.ulid[:8]}...)")
    print(f"   Status: {kernel1.data.get('status')}")
    print(f"   Initialized: {kernel1.data.get('_initialized')}")
    
    # Drugie wywołanie - zwróci istniejący
    kernel2 = await Being.get_or_create(
        kernel_soul,
        alias="system_kernel", 
        attributes={"status": "running"},  # Aktualizuje status
        unique_by="soul_hash"
    )
    print(f"   Drugi kernel: {kernel2.alias} ({kernel2.ulid[:8]}...)")
    print(f"   Status: {kernel2.data.get('status')}")
    print(f"   To samo Being: {kernel1.ulid == kernel2.ulid}")
    
    print("\n2. 💬 Message Beings - multi-instance pattern")
    
    # Każdy message to nowy Being
    message1 = await Being.create(
        message_soul,
        alias="msg_001",
        attributes={
            "content": "Hello world!", 
            "author": "user1",
            "timestamp": "2025-01-01T10:00:00Z"
        }
    )
    print(f"   Message 1: {message1.alias} ({message1.ulid[:8]}...)")
    print(f"   Content: {message1.data.get('content')}")
    print(f"   Initialized: {message1.data.get('_initialized')}")
    
    message2 = await Being.create(
        message_soul,
        alias="msg_002", 
        attributes={
            "content": "How are you?",
            "author": "user2", 
            "timestamp": "2025-01-01T10:01:00Z"
        }
    )
    print(f"   Message 2: {message2.alias} ({message2.ulid[:8]}...)")
    print(f"   Content: {message2.data.get('content')}")
    print(f"   Different Being: {message1.ulid != message2.ulid}")
    
    print("\n3. 🔄 User Session - get_or_create by alias")
    
    user_session_genotype = {
        "genesis": {"name": "user_session", "version": "1.0"},
        "attributes": {
            "user_id": {"py_type": "str"},
            "login_time": {"py_type": "str"},
            "last_activity": {"py_type": "str"}
        },
        "functions": {
            "init": {
                "py_type": "function"
            }
        },
        "module_source": '''
def init(being_context=None):
    """Initialize user session"""
    from datetime import datetime
    print(f"Session initialized for: {being_context.get('alias')}")
    return {"session_ready": True, "init_time": datetime.now().isoformat()}
'''
    }
    
    session_soul = await Soul.create(user_session_genotype, "user_session")
    
    # Primeira sesja dla user123
    session1 = await Being.get_or_create(
        session_soul,
        alias="session_user123",
        attributes={"user_id": "user123", "login_time": "2025-01-01T09:00:00Z"},
        unique_by="alias"
    )
    print(f"   Session 1: {session1.alias} ({session1.ulid[:8]}...)")
    print(f"   User ID: {session1.data.get('user_id')}")
    
    # Druga próba - zwróci istniejącą
    session2 = await Being.get_or_create(
        session_soul,
        alias="session_user123",
        attributes={"last_activity": "2025-01-01T09:30:00Z"},  # Aktualizuje
        unique_by="alias"
    )
    print(f"   Session 2: {session2.alias} ({session2.ulid[:8]}...)")
    print(f"   Last activity: {session2.data.get('last_activity')}")
    print(f"   Same session: {session1.ulid == session2.ulid}")
    
    print("\n4. 🧪 Test funkcji Soul")
    
    # Test wywołania funkcji
    kernel_status = await kernel1.execute_soul_function('get_status')
    if kernel_status.get('success'):
        result = kernel_status['data']['result']
        print(f"   Kernel status: {result}")
    
    print("\n✅ Demo zakończone!")

if __name__ == "__main__":
    asyncio.run(demo_get_or_create())
