# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-10-18 20:04
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lytyfy_rest', '0012_project_customer_img'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoanTerm',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tenure', models.IntegerField()),
                ('rate', models.FloatField()),
            ],
        ),
        migrations.AlterField(
            model_name='lenderdeviabtransaction',
            name='customer_email',
            field=models.CharField(max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='lenderdeviabtransaction',
            name='customer_name',
            field=models.CharField(max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='lenderdeviabtransaction',
            name='error_message',
            field=models.CharField(max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='lenderdeviabtransaction',
            name='notification',
            field=models.CharField(max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='lenderdeviabtransaction',
            name='product_info',
            field=models.CharField(max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='terms',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='lytyfy_rest.LoanTerm'),
        ),
    ]
