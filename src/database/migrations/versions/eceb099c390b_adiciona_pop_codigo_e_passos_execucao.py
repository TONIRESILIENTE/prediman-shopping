"""adiciona pop_codigo e passos_execucao

Revision ID: eceb099c390b
Revises: 701c811f8af8
Create Date: 2026-09-28 19:04:13.892528

Nota: os `alter_column` de UUID -> String(36) gerados pelo autogenerate
foram removidos manualmente. Eles sao falsos positivos: os models usam
String(36) para os IDs, a migracao inicial criou como UUID(), e o
Postgres representa os dois de forma equivalente. Aplicar essas conversoes
seria lento, arriscado e desnecessario.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'eceb099c390b'
down_revision: Union[str, None] = '701c811f8af8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tabela nova: passos_execucao (checklist obrigatorio com foto)
    op.create_table('passos_execucao',
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.Column('ordem_servico_id', sa.UUID(), nullable=False),
                    sa.Column('pop_codigo', sa.String(
                        length=20), nullable=True),
                    sa.Column('numero_passo', sa.Integer(), nullable=False),
                    sa.Column('descricao', sa.Text(), nullable=False),
                    sa.Column('concluido', sa.Boolean(), nullable=True),
                    sa.Column('foto_url', sa.String(
                        length=500), nullable=True),
                    sa.Column('timestamp_conclusao', sa.DateTime(
                        timezone=True), nullable=True),
                    sa.Column('tipo_passo', sa.String(
                        length=20), nullable=True),
                    sa.Column('validacao_ia', sa.String(
                        length=50), nullable=True),
                    sa.Column('validado', sa.Boolean(), nullable=True),
                    sa.ForeignKeyConstraint(['ordem_servico_id'], [
                                            'ordens_servico.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    # Coluna nova: ordens_servico.pop_codigo (vinculo com o POP)
    op.add_column('ordens_servico', sa.Column(
        'pop_codigo', sa.String(length=20), nullable=True))


def downgrade() -> None:
    # Reverte na ordem inversa
    op.drop_column('ordens_servico', 'pop_codigo')
    op.drop_table('passos_execucao')
