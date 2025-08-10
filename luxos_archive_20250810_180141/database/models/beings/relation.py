# 1. Tworzymy genotyp relacji
relationship_genotype = {
    "genesis": {
        "name": "basic_relationship",
        "type": "relation",
        "doc": "Podstawowa relacja między bytami"
    },
    "attributes": {
        "source_uid": {"py_type": "str"},
        "target_uid": {"py_type": "str"},
        "relation_type": {"py_type": "str"},
        "strength": {"py_type": "float"},
        "vector_1536": {"py_type": "List[float]"},
    }
}

# 2. Tworzymy duszę relacji
relationship_soul = await Soul.create(relationship_genotype, alias="basic_relation")

# 3. Tworzymy byt relacji
relationship_being = await Being.create(
    relationship_soul, 
    {
        "source_uid": "byt_a_uid",
        "target_uid": "byt_b_uid", 
        "relation_type": "communication",
        "strength": 0.8,
        "metadata": {"timestamp": "2025-01-29", "context": "system_interaction"}
    },
    limit=None
)