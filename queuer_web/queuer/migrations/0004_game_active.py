# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('queuer', '0003_game'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='active',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
