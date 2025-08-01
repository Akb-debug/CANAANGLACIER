from .models import Categorie

def categories_context(request):
    return {'categories': Categorie.objects.all()}
