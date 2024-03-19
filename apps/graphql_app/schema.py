from .services.schema_auto_generator import SchemaAutoGenerator


schema_generator = SchemaAutoGenerator()
schema = schema_generator.make_schema()
