"""
Walidatory dla LuxDB.
"""

from typing import Dict, Any, List, Tuple
from .types import SUPPORTED_TYPES

def validate_genotype(genotype: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Waliduje genotyp Soul.

    Args:
        genotype: Słownik z definicją genotypu

    Returns:
        Tuple (is_valid, errors)
    """
    errors = []

    # Sprawdź wymagane sekcje
    required_sections = ["genesis"]
    for section in required_sections:
        if section not in genotype:
            errors.append(f"Missing required section: {section}")

    # Sprawdź sekcję genesis
    if "genesis" in genotype:
        genesis = genotype["genesis"]
        if not isinstance(genesis, dict):
            errors.append("Genesis section must be a dictionary")
        else:
            # Sprawdź wymagane pola w genesis
            required_genesis_fields = ["name", "type"]
            for field in required_genesis_fields:
                if field not in genesis:
                    errors.append(f"Missing required genesis field: {field}")

    # Sprawdź sekcję attributes jeśli istnieje
    if "attributes" in genotype:
        attributes = genotype["attributes"]
        if not isinstance(attributes, dict):
            errors.append("Attributes section must be a dictionary")
        elif not attributes:  # Pusta sekcja attributes
            errors.append("Attributes section cannot be empty")
        else:
            # Waliduj każdy atrybut
            for attr_name, attr_config in attributes.items():
                if not isinstance(attr_config, dict):
                    errors.append(f"Attribute '{attr_name}' must be a dictionary")
                    continue

                # Sprawdź typ
                py_type = attr_config.get("py_type", "str")
                if py_type not in SUPPORTED_TYPES:
                    errors.append(f"Unsupported py_type '{py_type}' for attribute '{attr_name}'")

    # Sprawdź sekcję functions jeśli istnieje
    if "functions" in genotype:
        functions = genotype["functions"]
        if not isinstance(functions, dict):
            errors.append("Functions section must be a dictionary")
        else:
            # Waliduj każdą funkcję
            for func_name, func_config in functions.items():
                if not isinstance(func_config, dict):
                    errors.append(f"Function '{func_name}' must be a dictionary")
                    continue

                # Sprawdź wymagane pola funkcji
                if "py_type" not in func_config:
                    errors.append(f"Function '{func_name}' missing py_type")
                elif func_config["py_type"] != "function":
                    errors.append(f"Function '{func_name}' must have py_type 'function'")

                # Opcjonalne walidacje
                if "signature" in func_config and not isinstance(func_config["signature"], dict):
                    errors.append(f"Function '{func_name}' signature must be a dictionary")

    return len(errors) == 0, errors

def validate_genesis(genesis: Dict[str, Any]) -> List[str]:
    """
    Waliduje sekcję genesis genotypu.

    Args:
        genesis: Słownik z definicją genesis

    Returns:
        Lista błędów walidacji
    """
    errors = []

    # Wymagane pola
    required_fields = ["name", "version"]
    for field in required_fields:
        if field not in genesis:
            errors.append(f"Missing required field in genesis: {field}")
        elif not isinstance(genesis[field], str):
            errors.append(f"Field {field} in genesis must be string")

    # Opcjonalne pola
    optional_fields = {"description": str, "type": str}
    for field, expected_type in optional_fields.items():
        if field in genesis and not isinstance(genesis[field], expected_type):
            errors.append(f"Field {field} in genesis must be {expected_type.__name__}")

    return errors

def validate_attributes(attributes: Dict[str, Any]) -> List[str]:
    """
    Waliduje sekcję attributes genotypu.

    Args:
        attributes: Słownik z definicjami atrybutów

    Returns:
        Lista błędów walidacji
    """
    errors = []

    if not attributes:
        errors.append("Attributes section cannot be empty")
        return errors

    for attr_name, attr_config in attributes.items():
        attr_errors = validate_single_attribute(attr_name, attr_config)
        errors.extend(attr_errors)

    return errors

def validate_single_attribute(attr_name: str, attr_config: Dict[str, Any]) -> List[str]:
    """
    Waliduje pojedynczy atrybut.

    Args:
        attr_name: Nazwa atrybutu
        attr_config: Konfiguracja atrybutu

    Returns:
        Lista błędów walidacji
    """
    errors = []

    # Sprawdź typ atrybutu
    if "py_type" not in attr_config:
        errors.append(f"Missing py_type for attribute {attr_name}")
    else:
        py_type = attr_config["py_type"]
        if py_type not in SUPPORTED_TYPES:
            errors.append(f"Unsupported py_type '{py_type}' for attribute {attr_name}")

    # Waliduj specyficzne opcje dla typów
    py_type = attr_config.get("py_type")

    if py_type == "str":
        if "max_length" in attr_config:
            if not isinstance(attr_config["max_length"], int) or attr_config["max_length"] <= 0:
                errors.append(f"max_length for {attr_name} must be positive integer")

    elif py_type in ["int", "float"]:
        if "min_value" in attr_config:
            if not isinstance(attr_config["min_value"], (int, float)):
                errors.append(f"min_value for {attr_name} must be number")
        if "max_value" in attr_config:
            if not isinstance(attr_config["max_value"], (int, float)):
                errors.append(f"max_value for {attr_name} must be number")

    elif py_type == "List[float]":
        if "vector_size" in attr_config:
            if not isinstance(attr_config["vector_size"], int) or attr_config["vector_size"] <= 0:
                errors.append(f"vector_size for {attr_name} must be positive integer")

    # Waliduj boolean opcje
    boolean_options = ["unique", "nullable"]
    for option in boolean_options:
        if option in attr_config and not isinstance(attr_config[option], bool):
            errors.append(f"{option} for {attr_name} must be boolean")

    return errors

def validate_genes(genes: Dict[str, Any]) -> List[str]:
    """
    Waliduje sekcję genes genotypu.

    Args:
        genes: Słownik z definicjami genów

    Returns:
        Lista błędów walidacji
    """
    errors = []

    for gene_name, gene_path in genes.items():
        if not isinstance(gene_path, str):
            errors.append(f"Gene {gene_name} path must be string")
        elif not gene_path:
            errors.append(f"Gene {gene_name} path cannot be empty")

    return errors

def validate_being_data(data: Dict[str, Any], attributes: Dict[str, Any]) -> List[str]:
    """
    Waliduje dane Being względem definicji atrybutów.

    Args:
        data: Dane Being do walidacji
        attributes: Definicje atrybutów z genotypu

    Returns:
        Lista błędów walidacji
    """
    errors = []

    for attr_name, attr_config in attributes.items():
        value = data.get(attr_name)
        py_type = attr_config.get("py_type", "str")

        # Sprawdź wymagane pola
        if value is None:
            if "default" not in attr_config and not attr_config.get("nullable", False):
                errors.append(f"Missing required attribute: {attr_name}")
            continue

        # Sprawdź typ danych
        expected_type = SUPPORTED_TYPES.get(py_type)
        if expected_type and not isinstance(value, expected_type):
            errors.append(f"Attribute {attr_name} must be {py_type}, got {type(value).__name__}")

        # Waliduj specyficzne ograniczenia
        if py_type == "str" and isinstance(value, str):
            if "max_length" in attr_config and len(value) > attr_config["max_length"]:
                errors.append(f"Attribute {attr_name} exceeds max_length {attr_config['max_length']}")
            if "min_length" in attr_config and len(value) < attr_config["min_length"]:
                errors.append(f"Attribute {attr_name} below min_length {attr_config['min_length']}")

        elif py_type in ["int", "float"] and isinstance(value, (int, float)):
            if "min_value" in attr_config and value < attr_config["min_value"]:
                errors.append(f"Attribute {attr_name} below min_value {attr_config['min_value']}")
            if "max_value" in attr_config and value > attr_config["max_value"]:
                errors.append(f"Attribute {attr_name} above max_value {attr_config['max_value']}")

        elif py_type == "List[float]" and isinstance(value, list):
            if "vector_size" in attr_config and len(value) != attr_config["vector_size"]:
                errors.append(f"Attribute {attr_name} must have exactly {attr_config['vector_size']} elements")

    return errors