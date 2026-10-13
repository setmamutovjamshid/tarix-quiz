from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Question(models.Model):
    id = models.AutoField(primary_key=True)
    question = models.TextField(verbose_name="Savol matni")
    option_a = models.TextField(verbose_name="A varianti")
    option_b = models.TextField(verbose_name="B varianti")
    option_c = models.TextField(verbose_name="C varianti")
    option_d = models.TextField(verbose_name="D varianti")
    correct = models.SmallIntegerField(
        verbose_name="To'g'ri javob (0=A, 1=B, 2=C, 3=D)",
        validators=[MinValueValidator(0), MaxValueValidator(3)]
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Yaratilgan vaqti")

    class Meta:
        db_table = 'questions'
        ordering = ['id']
        verbose_name = "Savol"
        verbose_name_plural = "Savollar"

    def __str__(self):
        return f"#{self.id}: {self.question[:60]}"

    def to_public_dict(self):
        """Foydalanuvchiga to'g'ri javobni FOSh QILMASDAN savolni qaytarish"""
        return {
            'id': self.id,
            'question': self.question,
            'options': [
                self.option_a,
                self.option_b,
                self.option_c,
                self.option_d
            ]
        }

    def to_admin_dict(self):
        """Admin paneli uchun to'liq ma'lumot"""
        return {
            'id': self.id,
            'question': self.question,
            'option_a': self.option_a,
            'option_b': self.option_b,
            'option_c': self.option_c,
            'option_d': self.option_d,
            'options': [
                self.option_a,
                self.option_b,
                self.option_c,
                self.option_d
            ],
            'correct': self.correct,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }

    def to_export_dict(self):
        """Talab qilingan eksport formati: [{"q":"Savol","o":["A","B","C","D"],"a":1}]"""
        return {
            'q': self.question,
            'o': [
                self.option_a,
                self.option_b,
                self.option_c,
                self.option_d
            ],
            'a': int(self.correct)
        }
