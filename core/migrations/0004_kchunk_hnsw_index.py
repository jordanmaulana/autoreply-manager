from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_knowledge_knowledgechunk_socialaccount_replylog_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS kchunk_embedding_hnsw "
            "ON core_knowledgechunk USING hnsw (embedding vector_cosine_ops) "
            "WITH (m = 16, ef_construction = 64)",
            "DROP INDEX IF EXISTS kchunk_embedding_hnsw",
        ),
    ]
