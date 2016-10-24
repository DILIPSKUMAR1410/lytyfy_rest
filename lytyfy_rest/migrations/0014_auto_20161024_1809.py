# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-10-24 18:09
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('lytyfy_rest', '0013_auto_20161018_2004'),
    ]

    operations = [
        migrations.CreateModel(
            name='BorrowerDeviabTransaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('amount', models.FloatField(default=0.0)),
                ('payment_id', models.IntegerField(default=0)),
                ('status', models.CharField(max_length=30, null=True)),
                ('payment_mode', models.IntegerField(choices=[(0, b'CC'), (1, b'DC'), (2, b'NB'), (3, b'WL')], null=True)),
                ('transactions_type', models.IntegerField(choices=[(0, b'INST'), (1, b'DOWN')], null=True)),
            ],
        ),
        migrations.CreateModel(
            name='BorrowerLoanDetails',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.FloatField(default=0.0)),
                ('status', models.BooleanField(default=False)),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='FieldRep',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=30)),
                ('last_name', models.CharField(max_length=30, null=True)),
                ('mobile_number', models.CharField(blank=True, max_length=13, null=True)),
                ('email', models.CharField(max_length=60, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='fieldrep', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='FRBorrowerMap',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='LoanStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('principal_repaid', models.FloatField(default=0.0)),
                ('interest_repaid', models.FloatField(default=0.0)),
                ('principal_left', models.FloatField(default=0.0)),
                ('interest_left', models.FloatField(default=0.0)),
                ('emr', models.FloatField(default=0.0)),
                ('tenure_left', models.IntegerField()),
            ],
        ),
        migrations.RemoveField(
            model_name='borrower',
            name='project',
        ),
        migrations.AlterField(
            model_name='lendercurrentstatus',
            name='tenure_left',
            field=models.IntegerField(default=6),
        ),
        migrations.AddField(
            model_name='frborrowermap',
            name='borrower',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='borrower_fieldrep', to='lytyfy_rest.Borrower'),
        ),
        migrations.AddField(
            model_name='frborrowermap',
            name='field_rep',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fieldrep_borrower', to='lytyfy_rest.FieldRep'),
        ),
        migrations.AddField(
            model_name='borrowerloandetails',
            name='borrower',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='projects', to='lytyfy_rest.Borrower'),
        ),
        migrations.AddField(
            model_name='borrowerloandetails',
            name='current_status',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='borrower_loan_details', to='lytyfy_rest.LoanStatus'),
        ),
        migrations.AddField(
            model_name='borrowerloandetails',
            name='project',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='borrowers', to='lytyfy_rest.Project'),
        ),
        migrations.AddField(
            model_name='borrowerloandetails',
            name='terms',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='lytyfy_rest.LoanTerm'),
        ),
        migrations.AddField(
            model_name='borrowerdeviabtransaction',
            name='borrower',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='borrower_transactions', to='lytyfy_rest.Borrower'),
        ),
        migrations.AddField(
            model_name='borrowerdeviabtransaction',
            name='fieldrep',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='collections', to='lytyfy_rest.FieldRep'),
        ),
    ]
