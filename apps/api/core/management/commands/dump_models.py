# core/management/commands/dump_models.py
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import models
import json, pathlib

class Command(BaseCommand):
    help = "Dump installed models + fields for architecture audit"

    def handle(self, *args, **kwargs):
        out = {}

        for model in apps.get_models():
            meta = model._meta
            model_key = f"{meta.app_label}.{meta.object_name}"

            fields = {}
            for f in meta.get_fields():
                # Skip auto-created reverse relations and M2M intermediary tables
                if not isinstance(f, models.Field):
                    continue
                if f.many_to_many and f.auto_created:
                    continue

                fields[f.name] = {
                    "type": f.__class__.__name__,
                    "null": f.null,
                    "unique": getattr(f, "unique", False),
                    "pk": f.primary_key,
                    "related_to": (
                        getattr(f.remote_field, "model", None).__name__
                        if getattr(f, "remote_field", None)
                        else None
                    ),
                }

            out[model_key] = {
                "db_table": meta.db_table,
                "fields": fields,
                "indexes": [
                    ix.name or str(ix.fields) for ix in meta.indexes
                ],
            }

        dump_path = pathlib.Path("model_dump.json")
        dump_path.write_text(json.dumps(out, indent=2, sort_keys=True))
        self.stdout.write(self.style.SUCCESS(f"✓ Wrote {dump_path.resolve()}"))
