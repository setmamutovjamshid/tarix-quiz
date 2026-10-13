from django.core.management.base import BaseCommand
from quiz.models import Question

SAMPLE_QUESTIONS = [
    {
        "question": "Oʻzbekiston Respublikasi mustaqillikka qachon erishgan?",
        "option_a": "1990-yil 1-sentyabr",
        "option_b": "1991-yil 1-sentyabr",
        "option_c": "1992-yil 8-dekabr",
        "option_d": "1993-yil 2-iyul",
        "correct": 1
    },
    {
        "question": "Python dasturlash tilining asoschisi kim?",
        "option_a": "Gvido van Rossum (Guido van Rossum)",
        "option_b": "Brendan Eich",
        "option_c": "Jeyms Gosling",
        "option_d": "Bjarne Stroustrup",
        "correct": 0
    },
    {
        "question": "Dunyodagi eng katta va eng chuqur okean qaysi?",
        "option_a": "Atlantika okeani",
        "option_b": "Hind okeani",
        "option_c": "Shimoliy Muz okeani",
        "option_d": "Tinch okeani",
        "correct": 3
    },
    {
        "question": "Algoritm so'zi qaysi buyuk allomaning nomidan kelib chiqqan?",
        "option_a": "Abu Rayhon Beruniy",
        "option_b": "Al-Xorazmiy",
        "option_c": "Abu Ali ibn Sino",
        "option_d": "Mirzo Ulug'bek",
        "correct": 1
    },
    {
        "question": "O'zbekiston Respublikasining Konstitutsiyasi qachon qabul qilingan?",
        "option_a": "1991-yil 1-sentyabr",
        "option_b": "1992-yil 8-dekabr",
        "option_c": "1993-yil 9-aprel",
        "option_d": "1990-yil 24-mart",
        "correct": 1
    },
    {
        "question": "Web sahifalarning tuzilishi (skeleti) qaysi til orqali yaratiladi?",
        "option_a": "CSS",
        "option_b": "JavaScript",
        "option_c": "HTML",
        "option_d": "PHP",
        "correct": 2
    }
]

class Command(BaseCommand):
    help = "Bazaga namunaviy savollarni kiritish (seed data)"

    def handle(self, *args, **options):
        count = 0
        for item in SAMPLE_QUESTIONS:
            obj, created = Question.objects.get_or_create(
                question=item["question"],
                defaults={
                    "option_a": item["option_a"],
                    "option_b": item["option_b"],
                    "option_c": item["option_c"],
                    "option_d": item["option_d"],
                    "correct": item["correct"]
                }
            )
            if created:
                count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Muvaffaqiyatli: {count} ta yangi savol bazaga kiritildi. Jami savollar: {Question.objects.count()} ta.")
        )
