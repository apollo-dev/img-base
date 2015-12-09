# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('expt', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Composite',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('id_token', models.CharField(max_length=8)),
                ('current_region_unique', models.CharField(max_length=8)),
                ('current_zedge_unique', models.CharField(max_length=8)),
                ('experiment', models.ForeignKey(related_name='composites', to='expt.Experiment')),
                ('series', models.ForeignKey(related_name='composites', to='expt.Series')),
            ],
        ),
        migrations.CreateModel(
            name='DataFile',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('id_token', models.CharField(max_length=8)),
                ('data_type', models.CharField(max_length=255)),
                ('url', models.CharField(max_length=255)),
                ('file_name', models.CharField(max_length=255)),
                ('composite', models.ForeignKey(related_name='data_files', to='img.Composite')),
                ('experiment', models.ForeignKey(related_name='data_files', to='expt.Experiment')),
                ('series', models.ForeignKey(related_name='data_files', to='expt.Series')),
            ],
        ),
        migrations.CreateModel(
            name='Gon',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('id_token', models.CharField(default='', max_length=8)),
                ('r', models.IntegerField(default=0)),
                ('c', models.IntegerField(default=0)),
                ('z', models.IntegerField(default=0)),
                ('t', models.IntegerField(default=-1)),
                ('rs', models.IntegerField(default=-1)),
                ('cs', models.IntegerField(default=-1)),
                ('zs', models.IntegerField(default=1)),
                ('channel', models.ForeignKey(related_name='gons', to='img.Channel')),
                ('composite', models.ForeignKey(to='img.Composite', null=True, related_name='gons')),
                ('experiment', models.ForeignKey(related_name='gons', to='expt.Experiment')),
                ('gon', models.ForeignKey(to='img.Gon', null=True, related_name='gons')),
                ('series', models.ForeignKey(related_name='gons', to='expt.Series')),
            ],
        ),
        migrations.CreateModel(
            name='Mask',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('id_token', models.CharField(default='', max_length=8)),
                ('url', models.CharField(max_length=255)),
                ('file_name', models.CharField(max_length=255)),
                ('r', models.IntegerField(default=0)),
                ('c', models.IntegerField(default=0)),
                ('z', models.IntegerField(default=0)),
                ('t', models.IntegerField(default=-1)),
                ('rs', models.IntegerField(default=-1)),
                ('cs', models.IntegerField(default=-1)),
            ],
        ),
        migrations.CreateModel(
            name='MaskChannel',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('composite', models.ForeignKey(related_name='mask_channels', to='img.Composite')),
            ],
        ),
        migrations.CreateModel(
            name='Mod',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('id_token', models.CharField(max_length=8)),
                ('algorithm', models.CharField(max_length=255)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('composite', models.ForeignKey(related_name='mods', to='img.Composite')),
            ],
        ),
        migrations.CreateModel(
            name='Path',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('url', models.CharField(max_length=255)),
                ('file_name', models.CharField(max_length=255)),
                ('t', models.IntegerField(default=0)),
                ('z', models.IntegerField(default=0)),
                ('channel', models.ForeignKey(related_name='paths', to='img.Channel')),
                ('composite', models.ForeignKey(related_name='paths', to='img.Composite')),
                ('gon', models.ForeignKey(related_name='paths', to='img.Gon')),
            ],
        ),
        migrations.CreateModel(
            name='Template',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('rx', models.CharField(max_length=255)),
                ('rv', models.CharField(max_length=255)),
                ('composite', models.ForeignKey(related_name='templates', to='img.Composite')),
            ],
        ),
        migrations.AddField(
            model_name='path',
            name='template',
            field=models.ForeignKey(related_name='paths', to='img.Template'),
        ),
        migrations.AddField(
            model_name='mask',
            name='channel',
            field=models.ForeignKey(related_name='masks', to='img.MaskChannel'),
        ),
        migrations.AddField(
            model_name='mask',
            name='composite',
            field=models.ForeignKey(to='img.Composite', null=True, related_name='masks'),
        ),
        migrations.AddField(
            model_name='mask',
            name='experiment',
            field=models.ForeignKey(related_name='masks', to='expt.Experiment'),
        ),
        migrations.AddField(
            model_name='mask',
            name='series',
            field=models.ForeignKey(related_name='masks', to='expt.Series'),
        ),
        migrations.AddField(
            model_name='mask',
            name='template',
            field=models.ForeignKey(to='img.Template', null=True, related_name='masks'),
        ),
        migrations.AddField(
            model_name='gon',
            name='template',
            field=models.ForeignKey(to='img.Template', null=True, related_name='gons'),
        ),
        migrations.AddField(
            model_name='datafile',
            name='template',
            field=models.ForeignKey(related_name='data_files', to='img.Template'),
        ),
        migrations.AddField(
            model_name='channel',
            name='composite',
            field=models.ForeignKey(related_name='channels', to='img.Composite'),
        ),
    ]
