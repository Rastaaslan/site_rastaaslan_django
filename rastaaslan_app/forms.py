from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import UserProfile, ForumTopic, ForumPost


class CustomAuthenticationForm(AuthenticationForm):
    """Formulaire personnalisé d'authentification"""
    username = forms.CharField(
        label="Nom d'utilisateur",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Nom d'utilisateur"})
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mot de passe'})
    )


class CustomUserCreationForm(UserCreationForm):
    """Formulaire personnalisé de création d'utilisateur"""
    email = forms.EmailField(
        required=True,
        label="Adresse e-mail",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Adresse e-mail'})
    )
    username = forms.CharField(
        label="Nom d'utilisateur",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Nom d'utilisateur"})
    )
    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mot de passe'})
    )
    password2 = forms.CharField(
        label="Confirmation du mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmez le mot de passe'})
    )
    
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
    
    def save(self, commit=True):
        user = super(CustomUserCreationForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            # Créer un profil utilisateur vide
            UserProfile.objects.create(user=user)
        return user


class UserProfileForm(forms.ModelForm):
    """Formulaire de mise à jour du profil utilisateur"""
    first_name = forms.CharField(
        label="Prénom",
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label="Nom",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label="Adresse e-mail",
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = UserProfile
        fields = ('avatar', 'bio', 'twitch_username')
        widgets = {
            'avatar': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'URL de votre avatar'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Parlez-nous de vous'}),
            'twitch_username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Votre nom d'utilisateur Twitch"})
        }
    
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
    
    def save(self, commit=True):
        profile = super(UserProfileForm, self).save(commit=False)
        if commit:
            # Mettre à jour les informations de l'utilisateur
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()
            
            profile.save()
        return profile


class CustomPasswordChangeForm(PasswordChangeForm):
    """Formulaire personnalisé de changement de mot de passe"""
    old_password = forms.CharField(
        label="Ancien mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Ancien mot de passe'})
    )
    new_password1 = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Nouveau mot de passe'})
    )
    new_password2 = forms.CharField(
        label="Confirmation du nouveau mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmez le nouveau mot de passe'})
    )


class ForumTopicForm(forms.ModelForm):
    """Formulaire de création et d'édition de sujet de forum"""
    class Meta:
        model = ForumTopic
        fields = ('title', 'category', 'content')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre du sujet'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control markdown-editor', 
                'rows': 8, 
                'placeholder': 'Contenu de votre sujet - Supporte la syntaxe Markdown'
            })
        }
        help_texts = {
            'content': 'Ce champ prend en charge la syntaxe Markdown pour le formatage du texte.'
        }
    
    def clean_title(self):
        title = self.cleaned_data['title']
        # Vérifier la longueur minimale du titre
        if len(title) < 5:
            raise ValidationError("Le titre doit comporter au moins 5 caractères.")
        return title
    
    def clean_content(self):
        content = self.cleaned_data['content']
        # Vérifier la longueur minimale du contenu
        if len(content) < 20:
            raise ValidationError("Le contenu doit comporter au moins 20 caractères.")
        return content


class ForumPostForm(forms.ModelForm):
    """Formulaire de création et d'édition de message de forum"""
    class Meta:
        model = ForumPost
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control markdown-editor', 
                'rows': 6, 
                'placeholder': 'Votre message - Supporte la syntaxe Markdown'
            })
        }
        help_texts = {
            'content': 'Ce champ prend en charge la syntaxe Markdown pour le formatage du texte. Utilisez @username pour mentionner un utilisateur.'
        }
    
    def clean_content(self):
        content = self.cleaned_data['content']
        # Vérifier la longueur minimale du contenu
        if len(content) < 5:
            raise ValidationError("Le message doit comporter au moins 5 caractères.")
        return content