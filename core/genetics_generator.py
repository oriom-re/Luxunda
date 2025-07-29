
"""
Generator genetyki dla automatycznego tworzenia genotypów na podstawie pól Being
"""

import inspect
import json
from typing import Dict, Any, List, Optional, Union, get_type_hints, get_origin, get_args
from dataclasses import fields, is_dataclass
from datetime import datetime
import hashlib

from database.models.base import Being, Soul


class GeneticsGenerator:
    """Generator automatycznych genotypów na podstawie struktury klasy Being"""
    
    TYPE_MAPPING = {
        str: "str",
        int: "int", 
        float: "float",
        bool: "bool",
        dict: "dict",
        list: "List[str]",
        List[str]: "List[str]",
        List[int]: "List[int]",
        List[float]: "List[float]",
        Optional[str]: "str",
        Optional[int]: "int",
        Optional[float]: "float",
        Optional[bool]: "bool",
    }
    
    TABLE_MAPPING = {
        "str": "_text",
        "int": "_numeric", 
        "float": "_numeric",
        "bool": "_boolean",
        "dict": "_json",
        "List[str]": "_json",
        "List[int]": "_json", 
        "List[float]": "_json"
    }

    @classmethod
    def analyze_being_fields(cls, being_class: type = Being) -> Dict[str, Any]:
        """Analizuje pola klasy Being i zwraca informacje o typach"""
        field_info = {}
        
        if is_dataclass(being_class):
            # Pobierz pola dataclass
            dataclass_fields = fields(being_class)
            type_hints = get_type_hints(being_class)
            
            for field in dataclass_fields:
                field_name = field.name
                field_type = type_hints.get(field_name, field.type)
                
                # Pomiń podstawowe pola systemowe
                if field_name in ['ulid', 'global_ulid', 'soul_hash', 'created_at', 'updated_at']:
                    continue
                    
                field_info[field_name] = {
                    'type': field_type,
                    'default': field.default if field.default is not field.default_factory else None,
                    'default_factory': field.default_factory if field.default_factory is not field.default_factory else None,
                    'py_type': cls._get_py_type_string(field_type),
                    'table_name': cls._get_table_name(field_type),
                    'nullable': cls._is_optional(field_type)
                }
        
        return field_info

    @classmethod
    def _get_py_type_string(cls, field_type) -> str:
        """Konwertuje typ Python na string reprezentację"""
        origin = get_origin(field_type)
        args = get_args(field_type)
        
        # Obsługa Optional[T]
        if origin is Optional or (origin is type(Union) and type(None) in args):
            non_none_args = [arg for arg in args if arg is not type(None)]
            if non_none_args:
                return cls.TYPE_MAPPING.get(non_none_args[0], "str")
        
        # Obsługa List[T]
        if origin is list:
            if args:
                inner_type = args[0]
                if inner_type is str:
                    return "List[str]"
                elif inner_type is int:
                    return "List[int]"
                elif inner_type is float:
                    return "List[float]"
            return "List[str]"
        
        return cls.TYPE_MAPPING.get(field_type, "str")

    @classmethod
    def _get_table_name(cls, field_type) -> str:
        """Określa nazwę tabeli na podstawie typu"""
        py_type = cls._get_py_type_string(field_type)
        return cls.TABLE_MAPPING.get(py_type, "_text")

    @classmethod
    def _is_optional(cls, field_type) -> bool:
        """Sprawdza czy pole jest opcjonalne"""
        origin = get_origin(field_type)
        args = get_args(field_type)
        return origin is Optional or (origin is type(Union) and type(None) in args)

    @classmethod
    def generate_genotype_from_class(cls, being_class: type) -> Dict[str, Any]:
        """
        Generuje prosty genotyp na podstawie klasy dziedziczącej po Being
        
        Args:
            being_class: Klasa dziedzicząca po Being
            
        Returns:
            Dict: Genotyp w formacie prostym
        """
        field_info = cls.analyze_being_fields(being_class)
        
        # Budowanie atrybutów genotypu w prostym formacie
        attributes = {}
        for field_name, info in field_info.items():
            attributes[field_name] = {
                "table_name": info['table_name'],
                "py_type": info['py_type']
            }
        
        genotype = {
            "attributes": attributes,
            "functions": {}  # Na razie puste, później rozbudujemy
        }
        
        return genotype

    @classmethod
    async def create_soul_from_class(cls, being_class: type, alias: str = None) -> Soul:
        """
        Tworzy Soul na podstawie klasy dziedziczącej po Being
        
        Args:
            being_class: Klasa dziedzicząca po Being
            alias: Opcjonalny alias dla Soul
            
        Returns:
            Soul: Nowy lub istniejący Soul z bazy danych
        """
        from database.models.base import Soul
        
        # Generuj genotyp z klasy
        genotype = cls.generate_genotype_from_class(being_class)
        
        # Oblicz hash genotypu
        genotype_hash = hashlib.sha256(
            json.dumps(genotype, sort_keys=True).encode()
        ).hexdigest()
        
        # Sprawdź czy Soul z tym hash już istnieje
        from database.soul_repository import SoulRepository
        existing_souls = await Soul.load_all()
        
        for soul in existing_souls:
            if soul and soul.soul_hash == genotype_hash:
                print(f"🔄 Znaleziono istniejący Soul: {soul.soul_hash[:8]}...")
                return soul
        
        # Jeśli nie istnieje, utwórz nowy
        soul = Soul()
        soul.alias = alias or f"{being_class.__name__}Soul"
        soul.genotype = genotype
        soul.soul_hash = genotype_hash
        
        result = await SoulRepository.save(soul)
        
        if result and result.get('success'):
            print(f"✅ Utworzono nowy Soul: {soul.soul_hash[:8]}... dla klasy {being_class.__name__}")
            return soul
        else:
            raise Exception(f"Failed to create soul for class {being_class.__name__}")

    @classmethod
    def generate_specialized_genotypes(cls) -> Dict[str, Dict[str, Any]]:
        """Generuje zestaw wyspecjalizowanych genotypów"""
        genotypes = {}
        
        # Genotyp dla prostych bytów danych
        genotypes['simple_data'] = cls.generate_basic_genotype(
            name="SimpleDataBeing",
            description="Prosty byt do przechowywania danych",
            include_fields=['alias', 'genotype'],
            custom_genes={
                "get_data": "core.genes.data.get_simple_data",
                "set_data": "core.genes.data.set_simple_data"
            }
        )
        
        # Genotyp dla bytów z relacjami
        genotypes['relational'] = cls.generate_basic_genotype(
            name="RelationalBeing", 
            description="Byt z możliwościami relacyjnymi",
            exclude_fields=[],
            custom_genes={
                "create_relation": "core.genes.relations.create_relation",
                "find_relations": "core.genes.relations.find_relations",
                "optimize_relations": "core.genes.relations.optimize_relations"
            }
        )
        
        # Genotyp dla bytów wykonawczych
        genotypes['executable'] = cls.generate_basic_genotype(
            name="ExecutableBeing",
            description="Byt z możliwościami wykonywania genów",
            custom_genes={
                "execute_gene": "core.genes.execution.execute_gene",
                "load_genes": "core.genes.execution.load_genes",
                "gene_registry": "core.genes.execution.gene_registry"
            }
        )
        
        # Genotyp dla komunikujących się bytów
        genotypes['communicative'] = cls.generate_basic_genotype(
            name="CommunicativeBeing",
            description="Byt z możliwościami komunikacji",
            custom_genes={
                "send_message": "core.genes.communication.send_message",
                "receive_message": "core.genes.communication.receive_message", 
                "broadcast": "core.genes.communication.broadcast"
            }
        )
        
        return genotypes

    @classmethod
    def validate_genotype(cls, genotype: Dict[str, Any]) -> Dict[str, Any]:
        """Waliduje poprawność genotypu"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Sprawdź wymagane sekcje
        required_sections = ['metadata', 'attributes', 'genes']
        for section in required_sections:
            if section not in genotype:
                validation_result["errors"].append(f"Brak wymaganej sekcji: {section}")
                validation_result["valid"] = False
        
        # Sprawdź atrybuty
        if 'attributes' in genotype:
            for attr_name, attr_config in genotype['attributes'].items():
                if 'py_type' not in attr_config:
                    validation_result["errors"].append(f"Atrybut {attr_name} nie ma zdefiniowanego py_type")
                    validation_result["valid"] = False
                
                if 'table_name' not in attr_config:
                    validation_result["warnings"].append(f"Atrybut {attr_name} nie ma zdefiniowanej table_name")
        
        # Sprawdź geny
        if 'genes' in genotype:
            for gene_name, gene_path in genotype['genes'].items():
                if not isinstance(gene_path, str) or '.' not in gene_path:
                    validation_result["warnings"].append(f"Gen {gene_name} ma podejrzaną ścieżkę: {gene_path}")
        
        return validation_result

    @classmethod
    def generate_genotype_documentation(cls, genotype: Dict[str, Any]) -> str:
        """Generuje dokumentację dla genotypu"""
        doc = f"""
# Genotyp: {genotype.get('metadata', {}).get('name', 'Unknown')}

## Opis
{genotype.get('metadata', {}).get('description', 'Brak opisu')}

## Metadata
- **Wersja**: {genotype.get('metadata', {}).get('version', 'N/A')}
- **Utworzono**: {genotype.get('metadata', {}).get('created_at', 'N/A')}
- **Generator**: {genotype.get('metadata', {}).get('generator', 'N/A')}
- **Liczba pól**: {genotype.get('metadata', {}).get('field_count', 0)}

## Atrybuty
"""
        
        attributes = genotype.get('attributes', {})
        for attr_name, attr_config in attributes.items():
            doc += f"""
### {attr_name}
- **Typ**: {attr_config.get('py_type', 'unknown')}
- **Tabela**: {attr_config.get('table_name', 'unknown')}
- **Nullable**: {attr_config.get('nullable', False)}
- **Opis**: {attr_config.get('description', 'Brak opisu')}
"""
        
        doc += "\n## Geny\n"
        genes = genotype.get('genes', {})
        for gene_name, gene_path in genes.items():
            doc += f"- **{gene_name}**: `{gene_path}`\n"
        
        constraints = genotype.get('constraints', {})
        if constraints:
            doc += f"""
## Ograniczenia
- **Max instancji**: {constraints.get('max_instances', 'Brak')}
- **Wymagane pola**: {', '.join(constraints.get('required_fields', []))}
- **Reguły walidacji**: {len(constraints.get('validation_rules', []))} reguł
"""
        
        return doc


# Pomocnicze funkcje dla genów
class BasicGenes:
    """Podstawowe geny dla wygenerowanych genotypów"""
    
    @staticmethod
    async def initialize_being(being: Being, *args, **kwargs):
        """Inicjalizuje byt z podstawowymi wartościami"""
        print(f"🧬 Inicjalizacja bytu {being.ulid}")
        return {"status": "initialized", "being_ulid": being.ulid}
    
    @staticmethod
    async def validate_being(being: Being, *args, **kwargs):
        """Waliduje integralność bytu"""
        print(f"✅ Walidacja bytu {being.ulid}")
        errors = []
        
        # Sprawdź czy ma wymagane pola
        if not hasattr(being, 'ulid') or not being.ulid:
            errors.append("Brak ULID")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    @staticmethod
    async def serialize_being(being: Being, *args, **kwargs):
        """Serializuje byt do słownika"""
        print(f"📦 Serializacja bytu {being.ulid}")
        return being.to_dict()
