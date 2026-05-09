import streamlit as st
import google.generativeai as genai
import speech_recognition as sr
from datetime import datetime, timedelta
import time
import threading
import subprocess
import sys
import os
import io
from PIL import Image
import json
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fpdf import FPDF
import base64

try:
    import av
    from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
    WEBRTC_AVAILABLE = True
except ImportError:
    WEBRTC_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from pyvis.network import Network
    PYVIS_AVAILABLE = True
except ImportError:
    PYVIS_AVAILABLE = False

def init_session_state():
    defaults = {
        'language_selected': False,
        'language': 'English',
        'authenticated': False,
        'current_user': None,
        'users_db': {},
        'theme': 'Dark Blue',
        'lamp_lit': False,
        'show_register': False,
        'intro_complete': False,
        'focus_mode_active': False,
        'focus_mode_start_time': None,
        'focus_duration': 25,
        'focus_break_duration': 5,
        'camera_active': False,
        'text_size': 'Medium',
        'premium_user': False,
        'subscription_tier': 'free',
        'focus_sessions_today': 0,
        'last_focus_date': None,
        'show_user_info': False,
        'show_app_info': False,
        'animation_enabled': True,
        'focus_consent_given': False,
        'focus_consent_step': 0,
        'focus_consent_declined': False,
        'parents_notified': False,
        'mind_map_used_today': False,
        'image_gen_used_today': False,
        'focus_used_today': False,
        'last_trial_date': None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

def check_and_reset_daily_trials():
    today = datetime.now().strftime("%Y-%m-%d")
    if st.session_state.last_trial_date != today:
        st.session_state.mind_map_used_today = False
        st.session_state.image_gen_used_today = False
        st.session_state.focus_used_today = False
        st.session_state.last_trial_date = today

def show_language_selector():
    if 'language_selected' not in st.session_state:
        st.session_state.language_selected = False
    if not st.session_state.language_selected:
        st.markdown("<style>.stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }</style>", unsafe_allow_html=True)
        st.markdown("<div style='display: flex; justify-content: center; align-items: center; min-height: 80vh; flex-direction: column;'><div style='font-size: 60px; font-weight: bold; color: #38bdf8; animation: pulse 2s infinite; margin-bottom: 10px;'>🧠 Mind Vision</div><div style='color: #94a3b8; font-size: 20px; margin-bottom: 40px;'>Choose Your Language / اختر لغتك / Choisissez votre langue / Selecciona tu idioma / Wähle deine Sprache</div></div><style>@keyframes pulse { 0% { opacity: 0.7; transform: scale(0.95); } 50% { opacity: 1; transform: scale(1.05); } 100% { opacity: 0.7; transform: scale(0.95); } }</style>", unsafe_allow_html=True)
        col1, col2, col3, col4, col5 = st.columns(5)
        languages = [("🇺🇸 English", "English"), ("🇸🇦 العربية", "العربية"), ("🇫🇷 Français", "Français"), ("🇪🇸 Español", "Español"), ("🇩🇪 Deutsch", "Deutsch")]
        cols = [col1, col2, col3, col4, col5]
        for i, (label, lang) in enumerate(languages):
            with cols[i]:
                if st.button(label, use_container_width=True, key=f"lang_{lang}"):
                    st.session_state.language = lang
                    st.session_state.language_selected = True
                    st.rerun()
        st.stop()

class ParentNotification:
    def __init__(self, smtp_server="smtp.gmail.com", smtp_port=587):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        
    def send_email(self, sender_email, sender_password, recipient_email, subject, body):
        try:
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
            server.quit()
            return True
        except Exception as e:
            print(f"Email error: {e}")
            return False
            
    def notify_parents_focus_declined(self, student_name, parent1_email, parent2_email, sender_email, sender_password):
        if not parent1_email and not parent2_email:
            return False
        subject = t.get('email_subject_focus')
        body = t.get('email_body_focus').format(student_name=student_name)
        success = True
        if parent1_email:
            success = success and self.send_email(sender_email, sender_password, parent1_email, subject, body)
        if parent2_email:
            success = success and self.send_email(sender_email, sender_password, parent2_email, subject, body)
        return success

parent_notifier = ParentNotification()
EMAIL_CONFIG = {'sender_email': 'seraglashin2011@gmail.com', 'sender_password': 'S@ser14sd'}

class TranslationSystem:
    def __init__(self):
        self.translations = {
            'English': {
                'app_title': 'Mind Vision',
                'app_subtitle': 'AI Studying Assistant',
                'login': 'Login',
                'register': 'Register',
                'username': 'Username',
                'password': 'Password',
                'email': 'Email',
                'confirm_password': 'Confirm Password',
                'welcome_back': 'Welcome Back',
                'create_account': 'Create Account',
                'toggle_lamp': 'Toggle Lamp',
                'settings': 'Settings',
                'user_profile': 'User Profile',
                'theme': 'Theme',
                'language': 'Language',
                'text_size': 'Text Size',
                'logout': 'Logout',
                'qa': 'Q&A',
                'quizzes': 'Quizzes',
                'periodic_table': 'Periodic Table',
                'image_gen': 'Image Studio',
                'focus_mode': 'Focus Mode',
                'premium': 'Premium',
                'free': 'Free',
                'upgrade_premium': 'Upgrade to Premium',
                'start_focus': 'Start Focus',
                'stop_focus': 'Stop',
                'reset_focus': 'Reset',
                'focus_duration': 'Focus Duration (min)',
                'break_duration': 'Break Duration (min)',
                'enable_camera': 'Enable Camera (Study Monitoring)',
                'focusing': 'Focusing... Stay focused!',
                'break_time': 'Break Time!',
                'ready': 'Ready to Start',
                'daily_limit_reached': 'Daily free limit reached. Upgrade to Premium for unlimited sessions!',
                'user_info': 'User Information',
                'app_info': 'App Information',
                'member_since': 'Member Since',
                'total_logins': 'Total Logins',
                'last_login': 'Last Login',
                'subscription': 'Subscription',
                'version': 'Version',
                'developed_by': 'Developed by',
                'contact': 'Contact',
                'features': 'Features',
                'close': 'Close',
                'choose_subject': 'Choose a subject',
                'choose_tone': 'Choose a tone',
                'choose_details': 'Choose details level',
                'choose_edu_level': 'Choose educational level',
                'get_answer': 'Get Answer',
                'generate_quiz': 'Generate Quiz',
                'choose_difficulty': 'Choose difficulty',
                'num_questions': 'Number of questions',
                'generate_image': 'Generate Image',
                'download_image': 'Download Image',
                'describe_image': 'Describe the image you want to generate',
                'upload_image_edit': 'Or upload an image to edit',
                'enter_question': 'Enter your question',
                'enter_topic': 'Enter your topic',
                'text': 'Text',
                'voice': 'Voice',
                'record_question': 'Record your question',
                'record_topic': 'Record your topic',
                'transcribing': 'Transcribing audio...',
                'generating': 'Generating...',
                'answer': 'Answer',
                'your_quiz': 'Your Quiz',
                'open_periodic_table': 'Open Periodic Table',
                'launching': 'Launching...',
                'success': 'Success',
                'error': 'Error',
                'warning': 'Warning',
                'info': 'Information',
                'small': 'Small',
                'medium': 'Medium',
                'large': 'Large',
                'extra_large': 'Extra Large',
                'animations': 'Animations',
                'enable_animations': 'Enable Animations',
                'premium_feature': 'Premium Feature',
                'unlock_premium': 'Unlock Premium to access unlimited focus sessions, camera monitoring, advanced statistics, and more!',
                'subscribe_now': 'Subscribe Now',
                'free_tier_limit': 'Free Tier: 1 session/day',
                'premium_tier_benefits': 'Premium Tier: Unlimited sessions + Camera + Stats + Custom themes',
                'focus_stats': 'Focus Statistics',
                'total_sessions': 'Total Sessions',
                'total_focus_time': 'Total Focus Time',
                'avg_session': 'Average Session',
                'current_streak': 'Current Streak',
                'parent1_email': "Mother's Email",
                'parent2_email': "Father's Email",
                'parent1_phone': "Mother's Phone Number",
                'parent2_phone': "Father's Phone Number",
                'parental_consent': 'Parental Consent Required',
                'consent_message_1': 'I understand that Focus Mode uses my device camera to help me stay accountable during study sessions.',
                'consent_message_2': 'I agree to use Focus Mode responsibly for educational purposes only.',
                'consent_message_3': 'I understand that my parents will be notified if I do not follow the study schedule.',
                'i_accept': 'I Accept',
                'i_decline': 'I Decline',
                'consent_required': 'You must accept all consent messages to use Focus Mode.',
                'parents_notified': 'Your parents have been notified via email.',
                'email_subject_focus': 'Mind Vision - Focus Mode Alert',
                'email_body_focus': 'Dear Parent,\n\nYour child {student_name} has declined the required consent for Focus Mode in the Mind Vision studying app.\n\nThis feature helps students maintain accountability during study sessions using a timer and optional camera monitoring.\n\nPlease discuss study habits with your child.\n\nBest regards,\nMind Vision Team',
                'all_consents_accepted': 'All consents accepted! You can now use Focus Mode.',
                'consent_step': 'Consent Step',
                'of': 'of',
                'student_email': 'Student Email',
                'required_field': 'This field is required',
                'passwords_mismatch': 'Passwords do not match',
                'account_created': 'Account created! Please login.',
                'login_success': 'Login successful!',
                'invalid_credentials': 'Invalid credentials!',
                'have_account': 'Already have an account? Login',
                'no_account': "Don't have an account? Register",
                'sessions_remaining': 'Sessions remaining today',
                'session_used': 'Free session used today',
                'study_planner': 'Study Planner',
                'career_explorer': 'Career Explorer',
                'mind_maps': 'Mind Maps',
                'select_subjects': 'Select Subjects',
                'session_duration': 'Session Duration',
                'subjects_per_day': 'Subjects per Day',
                'study_days': 'Study Days per Week',
                'generate_schedule': 'Generate Schedule',
                'your_schedule': 'Your Study Schedule',
                'career_field': 'Career Field',
                'career_question': 'Career Question',
                'get_career_info': 'Get Career Info',
                'medical_services': 'Medical Services',
                'marketing': 'Marketing',
                'business_finance': 'Business & Finance',
                'computer_science': 'Computer Science',
                'engineering': 'Engineering',
                'graphic_design': 'Graphic Design',
                'education': 'Education',
                'law': 'Law',
                'mind_map_topic': 'Mind Map Topic',
                'generate_mind_map': 'Generate Mind Map',
                'daily_trial_used': 'Daily free trial used. Upgrade to Premium for unlimited access!',
                'download_pdf': 'Download PDF',
                'study_technique': 'Study Technique',
                'pomodoro': 'Pomodoro (25+5 min)',
                'deep_focus': 'Deep Focus (90+20 min)',
                'full_hour': 'Full Hour (50+10 min)',
                'set_alarm': 'Set Alarm',
                'technique_tip': 'Study Technique Tip',
                'pomodoro_desc': 'Best for short, intense study sessions with frequent breaks',
                'deep_focus_desc': 'Ideal for deep work and complex problem solving',
                'full_hour_desc': 'Perfect for classroom-style learning and lectures'
            },
            'العربية': {
                'app_title': 'مايند فيجن',
                'app_subtitle': 'مساعد الدراسة بالذكاء الاصطناعي',
                'login': 'تسجيل الدخول',
                'register': 'إنشاء حساب',
                'username': 'اسم المستخدم',
                'password': 'كلمة المرور',
                'email': 'البريد الإلكتروني',
                'confirm_password': 'تأكيد كلمة المرور',
                'welcome_back': 'مرحباً بعودتك',
                'create_account': 'إنشاء حساب جديد',
                'toggle_lamp': 'تشغيل/إطفاء المصباح',
                'settings': 'الإعدادات',
                'user_profile': 'الملف الشخصي',
                'theme': 'السمة',
                'language': 'اللغة',
                'text_size': 'حجم الخط',
                'logout': 'تسجيل الخروج',
                'qa': 'سؤال وجواب',
                'quizzes': 'اختبارات',
                'periodic_table': 'الجدول الدوري',
                'image_gen': 'استوديو الصور',
                'focus_mode': 'وضع التركيز',
                'premium': 'مميز',
                'free': 'مجاني',
                'upgrade_premium': 'الترقية إلى المميز',
                'start_focus': 'بدء التركيز',
                'stop_focus': 'إيقاف',
                'reset_focus': 'إعادة تعيين',
                'focus_duration': 'مدة التركيز (دقيقة)',
                'break_duration': 'مدة الراحة (دقيقة)',
                'enable_camera': 'تفعيل الكاميرا (مراقبة الدراسة)',
                'focusing': 'جاري التركيز... حافظ على تركيزك!',
                'break_time': 'وقت الراحة!',
                'ready': 'جاهز للبدء',
                'daily_limit_reached': 'تم الوصول للحد اليومي المجاني. قم بالترقية إلى المميز لجلسات غير محدودة!',
                'user_info': 'معلومات المستخدم',
                'app_info': 'معلومات التطبيق',
                'member_since': 'عضو منذ',
                'total_logins': 'إجمالي تسجيلات الدخول',
                'last_login': 'آخر تسجيل دخول',
                'subscription': 'الاشتراك',
                'version': 'الإصدار',
                'developed_by': 'تم التطوير بواسطة',
                'contact': 'تواصل',
                'features': 'المميزات',
                'close': 'إغلاق',
                'choose_subject': 'اختر المادة',
                'choose_tone': 'اختر النبرة',
                'choose_details': 'اختر مستوى التفاصيل',
                'choose_edu_level': 'اختر المستوى التعليمي',
                'get_answer': 'احصل على الإجابة',
                'generate_quiz': 'إنشاء اختبار',
                'choose_difficulty': 'اختر الصعوبة',
                'num_questions': 'عدد الأسئلة',
                'generate_image': 'توليد صورة',
                'download_image': 'تحميل الصورة',
                'describe_image': 'صف الصورة التي تريد توليدها',
                'upload_image_edit': 'أو ارفع صورة للتعديل',
                'enter_question': 'أدخل سؤالك',
                'enter_topic': 'أدخل الموضوع',
                'text': 'نص',
                'voice': 'صوت',
                'record_question': 'سجل سؤالك',
                'record_topic': 'سجل موضوعك',
                'transcribing': 'جاري تحويل الصوت إلى نص...',
                'generating': 'جاري التوليد...',
                'answer': 'الإجابة',
                'your_quiz': 'اختبارك',
                'open_periodic_table': 'فتح الجدول الدوري',
                'launching': 'جاري التشغيل...',
                'success': 'نجاح',
                'error': 'خطأ',
                'warning': 'تحذير',
                'info': 'معلومات',
                'small': 'صغير',
                'medium': 'متوسط',
                'large': 'كبير',
                'extra_large': 'كبير جداً',
                'animations': 'الرسوم المتحركة',
                'enable_animations': 'تفعيل الرسوم المتحركة',
                'premium_feature': 'ميزة مميزة',
                'unlock_premium': 'قم بالترقية إلى المميز للوصول إلى جلسات غير محدودة، مراقبة الكاميرا، إحصائيات متقدمة، والمزيد!',
                'subscribe_now': 'اشترك الآن',
                'free_tier_limit': 'المجانية: جلسة واحدة يومياً',
                'premium_tier_benefits': 'المميزة: جلسات غير محدودة + كاميرا + إحصائيات + سمات مخصصة',
                'focus_stats': 'إحصائيات التركيز',
                'total_sessions': 'إجمالي الجلسات',
                'total_focus_time': 'إجمالي وقت التركيز',
                'avg_session': 'متوسط الجلسة',
                'current_streak': 'السلسلة الحالية',
                'parent1_email': 'بريد الأم الإلكتروني',
                'parent2_email': 'بريد الأب الإلكتروني',
                'parent1_phone': 'رقم هاتف الأم',
                'parent2_phone': 'رقم هاتف الأب',
                'parental_consent': 'موافقة ولي الأمر مطلوبة',
                'consent_message_1': 'أدرك أن وضع التركيز يستخدم كاميرا الجهاز لمساعدتي على البقاء ملتزماً أثناء جلسات الدراسة.',
                'consent_message_2': 'أوافق على استخدام وضع التركيز بشكل مسؤول للأغراض التعليمية فقط.',
                'consent_message_3': 'أدرك أن والدي سيتم إخطارهما إذا لم ألتزم بجدول الدراسة.',
                'i_accept': 'أوافق',
                'i_decline': 'أرفض',
                'consent_required': 'يجب قبول جميع رسائل الموافقة لاستخدام وضع التركيز.',
                'parents_notified': 'تم إخطار والديك عبر البريد الإلكتروني.',
                'email_subject_focus': 'مايند فيجن - تنبيه وضع التركيز',
                'email_body_focus': 'عزيزي ولي الأمر،\n\nرفض طفلك {student_name} الموافقة المطلوبة لوضع التركيز في تطبيق مايند فيجن.\n\nتساعد هذه الميزة الطلاب على الحفاظ على الالتزام أثناء جلسات الدراسة.\n\nيرجى مناقشة عادات الدراسة مع طفلك.\n\nمع التحية،\nفريق مايند فيجن',
                'all_consents_accepted': 'تم قبول جميع الموافقات! يمكنك الآن استخدام وضع التركيز.',
                'consent_step': 'خطوة الموافقة',
                'of': 'من',
                'student_email': 'بريد الطالب',
                'required_field': 'هذا الحقل مطلوب',
                'passwords_mismatch': 'كلمات المرور غير متطابقة',
                'account_created': 'تم إنشاء الحساب! يرجى تسجيل الدخول.',
                'login_success': 'تم تسجيل الدخول بنجاح!',
                'invalid_credentials': 'بيانات غير صحيحة!',
                'have_account': 'لديك حساب؟ تسجيل الدخول',
                'no_account': 'ليس لديك حساب؟ سجل الآن',
                'sessions_remaining': 'الجلسات المتبقية اليوم',
                'session_used': 'الجلسة المجانية المستخدمة اليوم',
                'study_planner': 'مخطط الدراسة',
                'career_explorer': 'استكشاف المسارات المهنية',
                'mind_maps': 'خرائط العقل',
                'select_subjects': 'اختر المواد',
                'session_duration': 'مدة الجلسة',
                'subjects_per_day': 'المواد في اليوم',
                'study_days': 'أيام الدراسة في الأسبوع',
                'generate_schedule': 'إنشاء الجدول',
                'your_schedule': 'جدولك الدراسي',
                'career_field': 'المجال المهني',
                'career_question': 'سؤال مهني',
                'get_career_info': 'احصل على معلومات مهنية',
                'medical_services': 'الخدمات الطبية',
                'marketing': 'التسويق',
                'business_finance': 'الأعمال والمالية',
                'computer_science': 'علوم الحاسب',
                'engineering': 'الهندسة',
                'graphic_design': 'التصميم الجرافيكي',
                'education': 'التعليم',
                'law': 'القانون',
                'mind_map_topic': 'موضوع خريطة العقل',
                'generate_mind_map': 'إنشاء خريطة العقل',
                'daily_trial_used': 'تم استخدام التجربة المجانية اليوم. قم بالترقية إلى المميز للوصول غير المحدود!',
                'download_pdf': 'تحميل PDF',
                'study_technique': 'تقنية الدراسة',
                'pomodoro': 'بومودورو (25+5 دقيقة)',
                'deep_focus': 'تركيز عميق (90+20 دقيقة)',
                'full_hour': 'ساعة كاملة (50+10 دقيقة)',
                'set_alarm': 'ضبط المنبه',
                'technique_tip': 'نصيحة تقنية الدراسة',
                'pomodoro_desc': 'الأفضل لجلسات دراسة قصيرة ومكثفة مع فترات راحة متكررة',
                'deep_focus_desc': 'مثالي للعمل العميق وحل المشكلات المعقدة',
                'full_hour_desc': 'مثالي للتعلم على طريقة الفصول الدراسية والمحاضرات'
            },
            'Français': {
                'app_title': 'Mind Vision',
                'app_subtitle': 'Assistant d\'Étude IA',
                'login': 'Connexion',
                'register': 'S\'inscrire',
                'username': 'Nom d\'utilisateur',
                'password': 'Mot de passe',
                'email': 'Email',
                'confirm_password': 'Confirmer le mot de passe',
                'welcome_back': 'Bon retour',
                'create_account': 'Créer un compte',
                'toggle_lamp': 'Allumer/Éteindre',
                'settings': 'Paramètres',
                'user_profile': 'Profil Utilisateur',
                'theme': 'Thème',
                'language': 'Langue',
                'text_size': 'Taille du texte',
                'logout': 'Déconnexion',
                'qa': 'Q&R',
                'quizzes': 'Quiz',
                'periodic_table': 'Tableau Périodique',
                'image_gen': 'Studio d\'Images',
                'focus_mode': 'Mode Concentration',
                'premium': 'Premium',
                'free': 'Gratuit',
                'upgrade_premium': 'Passer à Premium',
                'start_focus': 'Démarrer',
                'stop_focus': 'Arrêter',
                'reset_focus': 'Réinitialiser',
                'focus_duration': 'Durée (minutes)',
                'break_duration': 'Pause (minutes)',
                'enable_camera': 'Activer la caméra',
                'focusing': 'Concentration... Restez focus!',
                'break_time': 'Temps de pause!',
                'ready': 'Prêt à commencer',
                'daily_limit_reached': 'Limite journalière atteinte. Passez à Premium pour des sessions illimitées!',
                'user_info': 'Informations Utilisateur',
                'app_info': 'Informations App',
                'member_since': 'Membre depuis',
                'total_logins': 'Connexions totales',
                'last_login': 'Dernière connexion',
                'subscription': 'Abonnement',
                'version': 'Version',
                'developed_by': 'Développé par',
                'contact': 'Contact',
                'features': 'Fonctionnalités',
                'close': 'Fermer',
                'choose_subject': 'Choisir une matière',
                'choose_tone': 'Choisir le ton',
                'choose_details': 'Niveau de détails',
                'choose_edu_level': 'Niveau d\'études',
                'get_answer': 'Obtenir la réponse',
                'generate_quiz': 'Générer le quiz',
                'choose_difficulty': 'Choisir la difficulté',
                'num_questions': 'Nombre de questions',
                'generate_image': 'Générer l\'image',
                'download_image': 'Télécharger',
                'describe_image': 'Décrivez l\'image souhaitée',
                'upload_image_edit': 'Ou téléchargez une image',
                'enter_question': 'Entrez votre question',
                'enter_topic': 'Entrez le sujet',
                'text': 'Texte',
                'voice': 'Voix',
                'record_question': 'Enregistrer la question',
                'record_topic': 'Enregistrer le sujet',
                'transcribing': 'Transcription...',
                'generating': 'Génération...',
                'answer': 'Réponse',
                'your_quiz': 'Votre Quiz',
                'open_periodic_table': 'Ouvrir le tableau',
                'launching': 'Lancement...',
                'success': 'Succès',
                'error': 'Erreur',
                'warning': 'Avertissement',
                'info': 'Information',
                'small': 'Petit',
                'medium': 'Moyen',
                'large': 'Grand',
                'extra_large': 'Très grand',
                'animations': 'Animations',
                'enable_animations': 'Activer les animations',
                'premium_feature': 'Fonctionnalité Premium',
                'unlock_premium': 'Passez à Premium pour des sessions illimitées, caméra, statistiques avancées et plus!',
                'subscribe_now': 'S\'abonner',
                'free_tier_limit': 'Gratuit: 1 session/jour',
                'premium_tier_benefits': 'Premium: Illimité + Caméra + Stats + Thèmes',
                'focus_stats': 'Statistiques',
                'total_sessions': 'Sessions totales',
                'total_focus_time': 'Temps total',
                'avg_session': 'Session moyenne',
                'current_streak': 'Série actuelle',
                'sessions_remaining': 'Sessions restantes aujourd\'hui',
                'session_used': 'Session gratuite utilisée aujourd\'hui',
                'study_planner': 'Planificateur d\'Études',
                'career_explorer': 'Explorateur de Carrière',
                'mind_maps': 'Cartes Mentales',
                'select_subjects': 'Sélectionner les matières',
                'session_duration': 'Durée de session',
                'subjects_per_day': 'Matières par jour',
                'study_days': 'Jours d\'étude par semaine',
                'generate_schedule': 'Générer l\'emploi du temps',
                'your_schedule': 'Votre emploi du temps',
                'career_field': 'Domaine professionnel',
                'career_question': 'Question de carrière',
                'get_career_info': 'Obtenir les infos',
                'medical_services': 'Services Médicaux',
                'marketing': 'Marketing',
                'business_finance': 'Affaires & Finance',
                'computer_science': 'Informatique',
                'engineering': 'Ingénierie',
                'graphic_design': 'Design Graphique',
                'education': 'Éducation',
                'law': 'Droit',
                'mind_map_topic': 'Sujet de la carte mentale',
                'generate_mind_map': 'Générer la carte',
                'daily_trial_used': 'Essai gratuit quotidien utilisé. Passez à Premium pour un accès illimité!',
                'download_pdf': 'Télécharger PDF',
                'study_technique': 'Technique d\'étude',
                'pomodoro': 'Pomodoro (25+5 min)',
                'deep_focus': 'Focus Profond (90+20 min)',
                'full_hour': 'Heure Pleine (50+10 min)',
                'set_alarm': 'Régler l\'alarme',
                'technique_tip': 'Conseil de technique',
                'pomodoro_desc': 'Idéal pour les sessions courtes et intenses',
                'deep_focus_desc': 'Parfait pour le travail en profondeur',
                'full_hour_desc': 'Idéal pour l\'apprentissage en classe'
            },
            'Español': {
                'app_title': 'Mind Vision',
                'app_subtitle': 'Asistente de Estudio IA',
                'login': 'Iniciar Sesión',
                'register': 'Registrarse',
                'username': 'Usuario',
                'password': 'Contraseña',
                'email': 'Correo',
                'confirm_password': 'Confirmar contraseña',
                'welcome_back': 'Bienvenido de nuevo',
                'create_account': 'Crear cuenta',
                'toggle_lamp': 'Encender/Apagar',
                'settings': 'Configuración',
                'user_profile': 'Perfil',
                'theme': 'Tema',
                'language': 'Idioma',
                'text_size': 'Tamaño de texto',
                'logout': 'Cerrar sesión',
                'qa': 'Preguntas',
                'quizzes': 'Cuestionarios',
                'periodic_table': 'Tabla Periódica',
                'image_gen': 'Estudio de Imágenes',
                'focus_mode': 'Modo Enfoque',
                'premium': 'Premium',
                'free': 'Gratis',
                'upgrade_premium': 'Actualizar a Premium',
                'start_focus': 'Comenzar',
                'stop_focus': 'Detener',
                'reset_focus': 'Reiniciar',
                'focus_duration': 'Duración (min)',
                'break_duration': 'Descanso (min)',
                'enable_camera': 'Activar cámara',
                'focusing': 'Enfocándote... ¡Mantén la concentración!',
                'break_time': '¡Tiempo de descanso!',
                'ready': 'Listo para comenzar',
                'daily_limit_reached': 'Límite diario alcanzado. ¡Actualiza a Premium para sesiones ilimitadas!',
                'user_info': 'Información de Usuario',
                'app_info': 'Información de App',
                'member_since': 'Miembro desde',
                'total_logins': 'Total de accesos',
                'last_login': 'Último acceso',
                'subscription': 'Suscripción',
                'version': 'Versión',
                'developed_by': 'Desarrollado por',
                'contact': 'Contacto',
                'features': 'Características',
                'close': 'Cerrar',
                'choose_subject': 'Elige materia',
                'choose_tone': 'Elige tono',
                'choose_details': 'Nivel de detalle',
                'choose_edu_level': 'Nivel educativo',
                'get_answer': 'Obtener respuesta',
                'generate_quiz': 'Generar cuestionario',
                'choose_difficulty': 'Elige dificultad',
                'num_questions': 'Número de preguntas',
                'generate_image': 'Generar imagen',
                'download_image': 'Descargar',
                'describe_image': 'Describe la imagen deseada',
                'upload_image_edit': 'O sube una imagen',
                'enter_question': 'Escribe tu pregunta',
                'enter_topic': 'Escribe el tema',
                'text': 'Texto',
                'voice': 'Voz',
                'record_question': 'Grabar pregunta',
                'record_topic': 'Grabar tema',
                'transcribing': 'Transcribiendo...',
                'generating': 'Generando...',
                'answer': 'Respuesta',
                'your_quiz': 'Tu Cuestionario',
                'open_periodic_table': 'Abrir tabla periódica',
                'launching': 'Iniciando...',
                'success': 'Éxito',
                'error': 'Error',
                'warning': 'Advertencia',
                'info': 'Información',
                'small': 'Pequeño',
                'medium': 'Mediano',
                'large': 'Grande',
                'extra_large': 'Extra grande',
                'animations': 'Animaciones',
                'enable_animations': 'Activar animaciones',
                'premium_feature': 'Función Premium',
                'unlock_premium': 'Actualiza a Premium para sesiones ilimitadas, cámara, estadísticas avanzadas y más!',
                'subscribe_now': 'Suscribirse',
                'free_tier_limit': 'Gratis: 1 sesión/día',
                'premium_tier_benefits': 'Premium: Ilimitado + Cámara + Stats + Temas',
                'focus_stats': 'Estadísticas',
                'total_sessions': 'Sesiones totales',
                'total_focus_time': 'Tiempo total',
                'avg_session': 'Promedio',
                'current_streak': 'Racha actual',
                'sessions_remaining': 'Sesiones restantes hoy',
                'session_used': 'Sesión gratuita usada hoy',
                'study_planner': 'Planificador de Estudio',
                'career_explorer': 'Explorador de Carreras',
                'mind_maps': 'Mapas Mentales',
                'select_subjects': 'Seleccionar materias',
                'session_duration': 'Duración de sesión',
                'subjects_per_day': 'Materias por día',
                'study_days': 'Días de estudio por semana',
                'generate_schedule': 'Generar horario',
                'your_schedule': 'Tu horario de estudio',
                'career_field': 'Campo profesional',
                'career_question': 'Pregunta de carrera',
                'get_career_info': 'Obtener información',
                'medical_services': 'Servicios Médicos',
                'marketing': 'Marketing',
                'business_finance': 'Negocios y Finanzas',
                'computer_science': 'Ciencias de la Computación',
                'engineering': 'Ingeniería',
                'graphic_design': 'Diseño Gráfico',
                'education': 'Educación',
                'law': 'Derecho',
                'mind_map_topic': 'Tema del mapa mental',
                'generate_mind_map': 'Generar mapa',
                'daily_trial_used': 'Prueba diaria gratuita usada. ¡Actualiza a Premium para acceso ilimitado!',
                'download_pdf': 'Descargar PDF',
                'study_technique': 'Técnica de estudio',
                'pomodoro': 'Pomodoro (25+5 min)',
                'deep_focus': 'Enfoque Profundo (90+20 min)',
                'full_hour': 'Hora Completa (50+10 min)',
                'set_alarm': 'Configurar alarma',
                'technique_tip': 'Consejo de técnica',
                'pomodoro_desc': 'Mejor para sesiones cortas e intensas',
                'deep_focus_desc': 'Ideal para trabajo profundo',
                'full_hour_desc': 'Perfecto para aprendizaje tipo clase'
            },
            'Deutsch': {
                'app_title': 'Mind Vision',
                'app_subtitle': 'KI Lernassistent',
                'login': 'Anmelden',
                'register': 'Registrieren',
                'username': 'Benutzername',
                'password': 'Passwort',
                'email': 'E-Mail',
                'confirm_password': 'Passwort bestätigen',
                'welcome_back': 'Willkommen zurück',
                'create_account': 'Konto erstellen',
                'toggle_lamp': 'Lampe umschalten',
                'settings': 'Einstellungen',
                'user_profile': 'Benutzerprofil',
                'theme': 'Thema',
                'language': 'Sprache',
                'text_size': 'Textgröße',
                'logout': 'Abmelden',
                'qa': 'F&A',
                'quizzes': 'Quiz',
                'periodic_table': 'Periodensystem',
                'image_gen': 'Bildstudio',
                'focus_mode': 'Fokus-Modus',
                'premium': 'Premium',
                'free': 'Kostenlos',
                'upgrade_premium': 'Auf Premium upgraden',
                'start_focus': 'Fokus starten',
                'stop_focus': 'Stop',
                'reset_focus': 'Zurücksetzen',
                'focus_duration': 'Fokusdauer (Min)',
                'break_duration': 'Pausendauer (Min)',
                'enable_camera': 'Kamera aktivieren',
                'focusing': 'Konzentriere dich... Bleib fokussiert!',
                'break_time': 'Pausenzeit!',
                'ready': 'Bereit zum Start',
                'daily_limit_reached': 'Tageslimit erreicht. Upgraden Sie auf Premium für unbegrenzte Sitzungen!',
                'user_info': 'Benutzerinfo',
                'app_info': 'App-Info',
                'member_since': 'Mitglied seit',
                'total_logins': 'Gesamtanmeldungen',
                'last_login': 'Letzte Anmeldung',
                'subscription': 'Abonnement',
                'version': 'Version',
                'developed_by': 'Entwickelt von',
                'contact': 'Kontakt',
                'features': 'Funktionen',
                'close': 'Schließen',
                'choose_subject': 'Fach wählen',
                'choose_tone': 'Ton wählen',
                'choose_details': 'Detailstufe',
                'choose_edu_level': 'Bildungsniveau',
                'get_answer': 'Antwort erhalten',
                'generate_quiz': 'Quiz erstellen',
                'choose_difficulty': 'Schwierigkeit wählen',
                'num_questions': 'Anzahl Fragen',
                'generate_image': 'Bild erstellen',
                'download_image': 'Herunterladen',
                'describe_image': 'Beschreibe das gewünschte Bild',
                'upload_image_edit': 'Oder Bild hochladen',
                'enter_question': 'Frage eingeben',
                'enter_topic': 'Thema eingeben',
                'text': 'Text',
                'voice': 'Sprache',
                'record_question': 'Frage aufnehmen',
                'record_topic': 'Thema aufnehmen',
                'transcribing': 'Transkribiere...',
                'generating': 'Generiere...',
                'answer': 'Antwort',
                'your_quiz': 'Dein Quiz',
                'open_periodic_table': 'Periodensystem öffnen',
                'launching': 'Starte...',
                'success': 'Erfolg',
                'error': 'Fehler',
                'warning': 'Warnung',
                'info': 'Information',
                'small': 'Klein',
                'medium': 'Mittel',
                'large': 'Groß',
                'extra_large': 'Sehr groß',
                'animations': 'Animationen',
                'enable_animations': 'Animationen aktivieren',
                'premium_feature': 'Premium-Funktion',
                'unlock_premium': 'Upgraden Sie auf Premium für unbegrenzte Sitzungen, Kamera, erweiterte Statistiken und mehr!',
                'subscribe_now': 'Jetzt abonnieren',
                'free_tier_limit': 'Kostenlos: 1 Sitzung/Tag',
                'premium_tier_benefits': 'Premium: Unbegrenzt + Kamera + Statistiken + Themen',
                'focus_stats': 'Fokus-Statistiken',
                'total_sessions': 'Gesamtsitzungen',
                'total_focus_time': 'Gesamtzeit',
                'avg_session': 'Durchschnitt',
                'current_streak': 'Aktuelle Serie',
                'sessions_remaining': 'Verbleibende Sitzungen heute',
                'session_used': 'Kostenlose Sitzung heute genutzt',
                'study_planner': 'Lernplaner',
                'career_explorer': 'Karriere-Explorer',
                'mind_maps': 'Mind Maps',
                'select_subjects': 'Fächer auswählen',
                'session_duration': 'Sitzungsdauer',
                'subjects_per_day': 'Fächer pro Tag',
                'study_days': 'Lerntage pro Woche',
                'generate_schedule': 'Zeitplan erstellen',
                'your_schedule': 'Dein Lernplan',
                'career_field': 'Berufsfeld',
                'career_question': 'Karrierefrage',
                'get_career_info': 'Infos erhalten',
                'medical_services': 'Medizinische Dienste',
                'marketing': 'Marketing',
                'business_finance': 'Business & Finanzen',
                'computer_science': 'Informatik',
                'engineering': 'Ingenieurwesen',
                'graphic_design': 'Grafikdesign',
                'education': 'Bildung',
                'law': 'Recht',
                'mind_map_topic': 'Mind-Map-Thema',
                'generate_mind_map': 'Mind Map erstellen',
                'daily_trial_used': 'Tägliche Testversion genutzt. Upgraden Sie auf Premium für unbegrenzten Zugang!',
                'download_pdf': 'PDF herunterladen',
                'study_technique': 'Lerntechnik',
                'pomodoro': 'Pomodoro (25+5 Min)',
                'deep_focus': 'Tiefer Fokus (90+20 Min)',
                'full_hour': 'Volle Stunde (50+10 Min)',
                'set_alarm': 'Alarm stellen',
                'technique_tip': 'Technik-Tipp',
                'pomodoro_desc': 'Am besten für kurze, intensive Lerneinheiten',
                'deep_focus_desc': 'Ideal für Tiefenarbeit',
                'full_hour_desc': 'Perfekt für klassenähnliches Lernen'
            }
        }

    def get(self, key, lang=None):
        if lang is None:
            lang = st.session_state.get('language', 'English')
        return self.translations.get(lang, self.translations['English']).get(key, key)

t = TranslationSystem()

class ThemeEngine:
    def __init__(self):
        self.themes = self._build_all_themes()

    def _build_all_themes(self):
        themes = {}
        
        def make_theme(name, bg, secondary_bg, text, accent, sidebar, card, border, success, warning, error, desc=""):
            return {
                'name': name,
                'bg': bg,
                'secondary_bg': secondary_bg,
                'text': text,
                'accent': accent,
                'sidebar_bg': sidebar,
                'card_bg': card,
                'border': border,
                'success': success,
                'warning': warning,
                'error': error,
                'description': desc
            }

        themes['Dark Blue'] = make_theme('Dark Blue', '#0a0e27', '#1a1f3a', '#ffffff', '#4a9eff', '#11152b', '#1e2542', '#2a3a5c', '#00d4aa', '#ffb347', '#ff6b6b', 'Deep space focus')
        themes['Dark Purple'] = make_theme('Dark Purple', '#0d0d1a', '#1a1a2e', '#eaeaea', '#a855f7', '#16162a', '#252545', '#3d3d6b', '#10b981', '#f59e0b', '#ef4444', 'Mystic creative energy')
        themes['Dark Green'] = make_theme('Dark Green', '#0a1f0a', '#0d2818', '#e8f5e9', '#4ade80', '#051405', '#143320', '#225533', '#22c55e', '#eab308', '#dc2626', 'Natural forest calm')
        themes['Dark Red'] = make_theme('Dark Red', '#1a0a0a', '#2d1212', '#fef2f2', '#f87171', '#1f0b0b', '#3d1f1f', '#5c2e2e', '#ef4444', '#fbbf24', '#dc2626', 'Bold crimson focus')
        themes['Dark Orange'] = make_theme('Dark Orange', '#1a0f0a', '#2d1a12', '#fef3c7', '#fb923c', '#1f120b', '#3d2317', '#5c3526', '#84cc16', '#fbbf24', '#f87171', 'Warm sunset energy')
        themes['Cyberpunk'] = make_theme('Cyberpunk', '#0a0a0a', '#1a0a1a', '#00ff41', '#ff00ff', '#0f050f', '#1f0f1f', '#ff0080', '#00ff41', '#ffff00', '#ff0040', 'Neon futuristic vibes')
        themes['Midnight Galaxy'] = make_theme('Midnight Galaxy', '#0b0d17', '#1a1d3a', '#e2e8f0', '#818cf8', '#13162b', '#252b4d', '#4f46e5', '#6366f1', '#f472b6', '#ef4444', 'Starry night theme')
        themes['Dark Teal'] = make_theme('Dark Teal', '#0a1a1a', '#0d2b2b', '#e0f2f1', '#26a69a', '#051a1a', '#143d3d', '#225555', '#00897b', '#ffca28', '#e53935', 'Deep ocean mystery')
        themes['Dark Rose'] = make_theme('Dark Rose', '#1a0a12', '#2d1a22', '#fce4ec', '#f48fb1', '#1f0b15', '#3d1f2b', '#5c2e40', '#ec407a', '#ffcc80', '#d32f2f', 'Romantic dark elegance')
        themes['Dark Gold'] = make_theme('Dark Gold', '#1a150a', '#2d2512', '#fff8e1', '#ffc107', '#1f1a0b', '#3d3317', '#5c4d26', '#ffb300', '#ff6f00', '#c62828', 'Luxurious golden night')
        themes['Dark Slate'] = make_theme('Dark Slate', '#0f1419', '#1e293b', '#f1f5f9', '#64748b', '#1a202c', '#334155', '#475569', '#10b981', '#f59e0b', '#ef4444', 'Professional slate dark')
        themes['Dark Berry'] = make_theme('Dark Berry', '#1a0a1a', '#2d1a2d', '#f3e5f5', '#ce93d8', '#1f0b1f', '#3d1f3d', '#5c2e5c', '#ab47bc', '#ff8a65', '#c62828', 'Rich berry tones')
        themes['Dark Amber'] = make_theme('Dark Amber', '#1a1205', '#2d2212', '#fff3e0', '#ff8f00', '#1f1608', '#3d2b17', '#5c4026', '#ef6c00', '#ffa000', '#bf360c', 'Warm amber glow')
        themes['Dark Indigo'] = make_theme('Dark Indigo', '#0a0a1a', '#1a1a3a', '#e8eaf6', '#7986cb', '#0b0b2b', '#1f1f4d', '#2e2e6b', '#5c6bc0', '#ffca28', '#e53935', 'Deep indigo wisdom')
        themes['Dark Coral'] = make_theme('Dark Coral', '#1a0f0f', '#2d1a1a', '#ffebee', '#ff7043', '#1f1212', '#3d2525', '#5c3838', '#ff5722', '#ffab91', '#bf360c', 'Vibrant coral night')
        themes['Light Mode'] = make_theme('Light Mode', '#ffffff', '#f5f5f5', '#000000', '#6200ee', '#eeeeee', '#ffffff', '#e0e0e0', '#4caf50', '#ff9800', '#f44336', 'Clean bright interface')
        themes['Nature Green'] = make_theme('Nature Green', '#e8f5e9', '#c8e6c9', '#1b5e20', '#2e7d32', '#a5d6a7', '#ffffff', '#81c784', '#388e3c', '#f57c00', '#d32f2f', 'Fresh botanical calm')
        themes['Ocean Blue'] = make_theme('Ocean Blue', '#e3f2fd', '#bbdefb', '#0d47a1', '#1976d2', '#90caf9', '#ffffff', '#64b5f6', '#0288d1', '#fbc02d', '#d32f2f', 'Peaceful aquatic flow')
        themes['Sunset Orange'] = make_theme('Sunset Orange', '#fff3e0', '#ffe0b2', '#bf360c', '#e65100', '#ffcc80', '#ffffff', '#ff9800', '#e65100', '#ff6d00', '#dd2c00', 'Warm golden glow')
        themes['Forest Green'] = make_theme('Forest Green', '#e8f5e9', '#c8e6c9', '#004d40', '#1b5e20', '#a5d6a7', '#ffffff', '#4caf50', '#2e7d32', '#827717', '#c62828', 'Deep earthy tones')
        themes['Spring Blossom'] = make_theme('Spring Blossom', '#fce4ec', '#f8bbd9', '#4a148c', '#880e4f', '#f48fb1', '#ffffff', '#ec407a', '#ad1457', '#ff6f00', '#c2185b', 'Gentle pink softness')
        themes['Coffee Break'] = make_theme('Coffee Break', '#efebe9', '#d7ccc8', '#3e2723', '#5d4037', '#bcaaa4', '#ffffff', '#a1887f', '#4e342e', '#ff8f00', '#bf360c', 'Warm cozy browns')
        themes['Cloud White'] = make_theme('Cloud White', '#fafafa', '#f0f0f0', '#212121', '#607d8b', '#e0e0e0', '#ffffff', '#bdbdbd', '#546e7a', '#ffca28', '#e53935', 'Soft cloudy minimal')
        themes['Lavender Mist'] = make_theme('Lavender Mist', '#f3e5f5', '#e1bee7', '#4a148c', '#7b1fa2', '#ce93d8', '#ffffff', '#ba68c8', '#6a1b9a', '#ff8a65', '#c62828', 'Soft lavender fields')
        themes['Mint Fresh'] = make_theme('Mint Fresh', '#e0f2f1', '#b2dfdb', '#004d40', '#00897b', '#80cbc4', '#ffffff', '#4db6ac', '#00695c', '#ffa726', '#bf360c', 'Cool mint refresh')
        themes['Peach Soft'] = make_theme('Peach Soft', '#fff3e0', '#ffe0b2', '#e65100', '#f57c00', '#ffcc80', '#ffffff', '#ffb74d', '#ef6c00', '#ffca28', '#d84315', 'Soft peach warmth')
        themes['Sky Blue'] = make_theme('Sky Blue', '#e1f5fe', '#b3e5fc', '#01579b', '#0288d1', '#81d4fa', '#ffffff', '#4fc3f7', '#0277bd', '#ffca28', '#e64a19', 'Clear sky serenity')
        themes['Lemon Zest'] = make_theme('Lemon Zest', '#fffde7', '#fff9c4', '#f57f17', '#fbc02d', '#fff59d', '#ffffff', '#fff176', '#f9a825', '#ff7043', '#e64a19', 'Bright citrus energy')
        themes['Cherry Blossom'] = make_theme('Cherry Blossom', '#fce4ec', '#f8bbd9', '#880e4f', '#c2185b', '#f48fb1', '#ffffff', '#f06292', '#ad1457', '#ff8a65', '#bf360c', 'Delicate sakura pink')
        themes['Arctic Ice'] = make_theme('Arctic Ice', '#e0f7fa', '#b2ebf2', '#006064', '#00acc1', '#80deea', '#ffffff', '#4dd0e1', '#00838f', '#ffca28', '#e64a19', 'Frozen arctic cool')
        themes['Tropical Paradise'] = make_theme('Tropical Paradise', '#e0f2f1', '#b2dfdb', '#00695c', '#ff6f00', '#80cbc4', '#ffffff', '#4db6ac', '#009688', '#ff8f00', '#e64a19', 'Exotic tropical vibes')
        themes['Neon Dreams'] = make_theme('Neon Dreams', '#0a0a0a', '#1a1a2e', '#00ff9f', '#ff00ff', '#16213e', '#0f3460', '#e94560', '#00fff5', '#ffff00', '#ff006e', 'Electric neon night')
        themes['Retro Wave'] = make_theme('Retro Wave', '#1a0a2e', '#2d1b4e', '#ff71ce', '#01cdfe', '#3d2b6e', '#4f3b8e', '#05ffa1', '#b967ff', '#fffb96', '#ff006e', '80s synthwave style')
        themes['Autumn Leaves'] = make_theme('Autumn Leaves', '#fff3e0', '#ffcc80', '#e65100', '#d84315', '#ffe0b2', '#ffffff', '#ffb74d', '#bf360c', '#8d6e63', '#3e2723', 'Fall foliage warmth')
        themes['Northern Lights'] = make_theme('Northern Lights', '#0d1b2a', '#1b263b', '#00ff88', '#00d4aa', '#415a77', '#778da9', '#e0e1dd', '#70e000', '#9ef01a', '#ff006e', 'Aurora borealis magic')
        themes['Desert Sand'] = make_theme('Desert Sand', '#fff8e1', '#ffecb3', '#ff6f00', '#e65100', '#ffe082', '#ffffff', '#ffd54f', '#bf360c', '#8d6e63', '#3e2723', 'Sahara golden dunes')
        themes['Galaxy Purple'] = make_theme('Galaxy Purple', '#0d0221', '#1a0b2e', '#e0aaff', '#c77dff', '#240046', '#3c096c', '#7b2cbf', '#9d4edd', '#ff6d00', '#ff006e', 'Deep space purple')
        themes['Coral Reef'] = make_theme('Coral Reef', '#e0f7fa', '#b2ebf2', '#00838f', '#ff7043', '#80deea', '#ffffff', '#4dd0e1', '#f4511e', '#ffca28', '#d84315', 'Underwater coral world')
        themes['Volcanic Fire'] = make_theme('Volcanic Fire', '#1a0505', '#2d0f0f', '#ff3d00', '#ff6d00', '#3d1f1f', '#4f2f2f', '#ff9100', '#ff1744', '#ffea00', '#bf360c', 'Magma and flames')
        themes['Emerald City'] = make_theme('Emerald City', '#0a1f0a', '#0d2e0d', '#00e676', '#69f0ae', '#1b5e20', '#2e7d32', '#4caf50', '#00c853', '#76ff03', '#1b5e20', 'Wizard of Oz green')
        themes['Royal Velvet'] = make_theme('Royal Velvet', '#0a0a1a', '#1a1a3a', '#ffd700', '#c0c0c0', '#2d2d5a', '#3d3d7a', '#b8860b', '#daa520', '#ffd700', '#8b0000', 'Royal gold and velvet')
        themes['Electric Blue'] = make_theme('Electric Blue', '#001a33', '#003366', '#00bfff', '#1e90ff', '#004080', '#0059b3', '#0099ff', '#00ccff', '#ffcc00', '#ff0066', 'High voltage blue')
        themes['Crimson Velvet'] = make_theme('Crimson Velvet', '#1a0000', '#330000', '#ff1744', '#ff5252', '#4d0000', '#660000', '#ff8a80', '#d50000', '#ffab91', '#b71c1c', 'Luxury red velvet')
        themes['Solar Flare'] = make_theme('Solar Flare', '#1a1000', '#332200', '#ffab00', '#ff6d00', '#4d3300', '#664400', '#ffd740', '#ff9100', '#ff3d00', '#bf360c', 'Sun energy explosion')
        themes['Moonlight Silver'] = make_theme('Moonlight Silver', '#0a0a0f', '#1a1a2e', '#c0c0c0', '#e8e8e8', '#2d2d3d', '#3d3d5d', '#a0a0b0', '#d0d0e0', '#ffd700', '#ff6d00', 'Elegant silver moon')
        themes['Matrix Code'] = make_theme('Matrix Code', '#000000', '#0d0208', '#00ff41', '#003b00', '#001a00', '#002900', '#008f11', '#00ff41', '#ffff00', '#ff0000', 'Digital rain matrix')
        themes['Stranger Things'] = make_theme('Stranger Things', '#0a0000', '#1a0000', '#ff2a6d', '#d30055', '#2a0000', '#3d0000', '#ff0055', '#ff1744', '#ffab91', '#b71c1c', 'Upside down red')
        themes['Tokyo Night'] = make_theme('Tokyo Night', '#0a0a1a', '#1a1a2e', '#7aa2f7', '#bb9af7', '#24283b', '#414868', '#73daca', '#7dcfff', '#e0af68', '#f7768e', 'Neon Tokyo streets')
        themes['Nordic Frost'] = make_theme('Nordic Frost', '#2e3440', '#3b4252', '#eceff4', '#88c0d0', '#434c5e', '#4c566a', '#81a1c1', '#5e81ac', '#ebcb8b', '#bf616a', 'Scandinavian winter')
        themes['Dracula'] = make_theme('Dracula', '#282a36', '#44475a', '#f8f8f2', '#bd93f9', '#6272a4', '#ffb86c', '#50fa7b', '#8be9fd', '#f1fa8c', '#ff79c6', 'Classic Dracula colors')
        themes['Gruvbox'] = make_theme('Gruvbox', '#282828', '#3c3836', '#ebdbb2', '#b8bb26', '#504945', '#665c54', '#fabd2f', '#fe8019', '#fb4934', '#d3869b', 'Retro warm terminal')
        themes['Monokai Pro'] = make_theme('Monokai Pro', '#2d2a2e', '#383539', '#fcfcfa', '#ffd866', '#403e41', '#5b595c', '#ff6188', '#a9dc76', '#78dce8', '#ab9df2', 'Professional code')
        themes['Synthwave 84'] = make_theme('Synthwave 84', '#241b2f', '#2b213a', '#f92aad', '#72f1b8', '#34294f', '#433364', '#f4f99d', '#fdfdfd', '#ff7edb', '#36f9f6', 'Outrun aesthetic')
        themes['Horizon'] = make_theme('Horizon', '#1c1e26', '#232530', '#e0e0e0', '#e95678', '#2e303e', '#6c6f93', '#fab795', '#59e3e3', '#f9cec3', '#21bfc2', 'Pastel horizon glow')
        themes['City Lights'] = make_theme('City Lights', '#0d1117', '#161b22', '#c9d1d9', '#58a6ff', '#21262d', '#30363d', '#79c0ff', '#a5d6ff', '#d29922', '#f85149', 'Urban night lights')

        return themes

    def get_theme(self, name):
        return self.themes.get(name, self.themes['Dark Blue'])

    def get_all_themes(self):
        return list(self.themes.keys())

    def generate_css(self, theme_name, text_size='Medium', animations=True):
        theme = self.get_theme(theme_name)
        
        sizes = {
            'Small': {'base': '14px', 'h1': '28px', 'h2': '22px', 'h3': '18px', 'h4': '16px'},
            'Medium': {'base': '16px', 'h1': '32px', 'h2': '26px', 'h3': '20px', 'h4': '18px'},
            'Large': {'base': '18px', 'h1': '36px', 'h2': '30px', 'h3': '24px', 'h4': '20px'},
            'Extra Large': {'base': '20px', 'h1': '40px', 'h2': '34px', 'h3': '28px', 'h4': '24px'}
        }
        sz = sizes.get(text_size, sizes['Medium'])

        anim_css = """
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes slideIn { from { transform: translateX(-100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }
        @keyframes glow { 0% { box-shadow: 0 0 5px """ + theme['accent'] + """; } 50% { box-shadow: 0 0 20px """ + theme['accent'] + """, 0 0 40px """ + theme['accent'] + """40; } 100% { box-shadow: 0 0 5px """ + theme['accent'] + """; } }
        @keyframes shimmer { 0% { background-position: -1000px 0; } 100% { background-position: 1000px 0; } }
        @keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
        @keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes scaleIn { from { transform: scale(0.8); opacity: 0; } to { transform: scale(1); opacity: 1; } }
        @keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-10px); } }
        .animate-fade { animation: fadeIn 0.6s ease-out; }
        .animate-slide { animation: slideIn 0.5s ease-out; }
        .animate-pulse { animation: pulse 2s infinite; }
        .animate-glow { animation: glow 2s infinite; }
        .animate-bounce { animation: bounce 2s infinite; }
        .animate-float { animation: float 3s ease-in-out infinite; }
        .animate-scale { animation: scaleIn 0.4s ease-out; }
        """ if animations else ""

        css = f"""
        <style>
        {anim_css}

        .stApp {{
            background: linear-gradient(135deg, {theme['bg']} 0%, {theme['secondary_bg']} 100%);
            color: {theme['text']};
            font-size: {sz['base']};
            transition: all 0.5s ease;
        }}

        .stSidebar {{
            background-color: {theme['sidebar_bg']} !important;
            transition: all 0.5s ease;
        }}

        .stButton>button {{
            background-color: {theme['accent']};
            color: {theme['bg']};
            border-radius: 12px;
            border: none;
            font-weight: 600;
            padding: 10px 24px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            animation: fadeIn 0.5s ease-out;
        }}

        .stButton>button:hover {{
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 8px 25px {theme['accent']}50;
            filter: brightness(1.1);
        }}

        .stButton>button:active {{
            transform: translateY(-1px) scale(0.98);
        }}

        .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div {{
            background-color: {theme['card_bg']};
            color: {theme['text']};
            border: 2px solid {theme['border']};
            border-radius: 10px;
            transition: all 0.3s ease;
            font-size: {sz['base']};
        }}

        .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {{
            border-color: {theme['accent']};
            box-shadow: 0 0 0 3px {theme['accent']}30;
            transform: translateY(-2px);
        }}

        .stSelectbox>div>div {{
            background-color: {theme['card_bg']};
            color: {theme['text']};
        }}

        .stRadio>div {{
            background-color: {theme['card_bg']};
            border-radius: 10px;
            padding: 10px;
        }}

        .stTabs [data-baseweb="tab-list"] {{
            background-color: {theme['sidebar_bg']};
            border-radius: 12px;
            padding: 5px;
        }}

        .stTabs [data-baseweb="tab"] {{
            color: {theme['text']};
            border-radius: 8px;
            transition: all 0.3s ease;
        }}

        .stTabs [data-baseweb="tab"]:hover {{
            background-color: {theme['accent']}20;
            transform: translateY(-2px);
        }}

        .stTabs [aria-selected="true"] {{
            background-color: {theme['accent']};
            color: {theme['bg']};
            font-weight: bold;
            box-shadow: 0 4px 15px {theme['accent']}40;
        }}

        .element-card {{
            background: {theme['card_bg']};
            border: 2px solid {theme['border']};
            border-radius: 16px;
            padding: 24px;
            margin: 12px 0;
            transition: all 0.3s ease;
            animation: fadeIn 0.6s ease-out;
        }}

        .element-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px {theme['accent']}20;
            border-color: {theme['accent']};
        }}

        h1 {{
            color: {theme['text']} !important;
            font-size: {sz['h1']} !important;
            animation: fadeIn 0.8s ease-out;
        }}

        h2 {{
            color: {theme['text']} !important;
            font-size: {sz['h2']} !important;
            animation: fadeIn 0.7s ease-out;
        }}

        h3 {{
            color: {theme['text']} !important;
            font-size: {sz['h3']} !important;
            animation: fadeIn 0.6s ease-out;
        }}

        h4 {{
            color: {theme['text']} !important;
            font-size: {sz['h4']} !important;
        }}

        .stMarkdown {{
            animation: fadeIn 0.5s ease-out;
        }}

        .stSpinner > div {{
            border-color: {theme['accent']} !important;
        }}

        .stAlert {{
            border-radius: 12px;
            border: 2px solid;
            animation: slideIn 0.4s ease-out;
        }}

        .stAlert[data-baseweb="notification"] {{
            background-color: {theme['card_bg']};
        }}

        ::-webkit-scrollbar {{
            width: 10px;
        }}

        ::-webkit-scrollbar-track {{
            background: {theme['bg']};
        }}

        ::-webkit-scrollbar-thumb {{
            background: {theme['accent']};
            border-radius: 5px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: {theme['accent']}dd;
        }}

        .premium-badge {{
            background: linear-gradient(135deg, #ffd700, #ffed4e);
            color: #000;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 12px;
            animation: pulse 2s infinite;
            display: inline-block;
        }}

        .timer-display {{
            font-size: 72px;
            font-weight: bold;
            text-align: center;
            color: {theme['accent']};
            font-family: 'Courier New', monospace;
            text-shadow: 0 0 20px {theme['accent']}40;
            animation: glow 2s infinite;
        }}

        [data-testid="stVerticalBlock"] > div {{
            animation: fadeIn 0.4s ease-out;
        }}

        .stTextInput:hover, .stTextArea:hover, .stSelectbox:hover {{
            transform: translateY(-2px);
        }}

        img {{
            transition: all 0.3s ease;
            border-radius: 12px;
        }}

        img:hover {{
            transform: scale(1.02);
            box-shadow: 0 8px 25px rgba(0,0,0,0.2);
        }}
        </style>
        """
        return css

theme_engine = ThemeEngine()

try:
    genai.configure(api_key='AIzaSyA1KBXnu7QtIOLmcMZxVDhQJlzKI8InGD4')
    model = genai.GenerativeModel('gemini-2.5-flash')
    ai_available = True
except Exception:
    ai_available = False
    model = None

try:
    from google import genai as genai_client
    client = genai_client.Client(api_key='c533f9a3c7abb314a4ff9b27c595239f')
    image_gen_available = True
except Exception:
    image_gen_available = False

def convert_audio(audio_file):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language='en-US')
            return text
    except sr.UnknownValueError:
        return "Could not understand the audio"
    except sr.RequestError:
        return "Speech recognition service error"
    except Exception as e:
        return f"Error: {str(e)}"

def show_intro():
    intro_html = """
    <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #0f172a; z-index: 9999; display: flex; justify-content: center; align-items: center; flex-direction: column; animation: fadeIn 1s ease-out;">
        <div style="font-size: 80px; font-weight: bold; color: #38bdf8; animation: pulse 2s infinite, float 3s ease-in-out infinite; display: flex; gap: 20px;">
            <span>M<span style="font-size: 120px; display: inline-block; animation: bounce 2s infinite;">i</span>nd</span>
            <span>V<span style="font-size: 120px; display: inline-block; animation: bounce 2s infinite 0.5s;">i</span>sion</span>
        </div>
        <div style="color: white; font-size: 24px; margin-top: 20px; animation: fadeIn 2s ease-out 1s both;">AI Studying Assistant</div>
        <div style="color: #94a3b8; margin-top: 10px; animation: fadeIn 2s ease-out 2s both;">Loading your personalized experience...</div>
        <div style="margin-top: 30px; width: 200px; height: 4px; background: #1e293b; border-radius: 2px; overflow: hidden;">
            <div style="width: 100%; height: 100%; background: linear-gradient(90deg, #38bdf8, #818cf8); animation: shimmer 2s infinite;"></div>
        </div>
    </div>
    <style>
    @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes pulse { 0% { opacity: 0.6; transform: scale(0.95); } 50% { opacity: 1; transform: scale(1.05); } 100% { opacity: 0.6; transform: scale(0.95); } }
    @keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-20px); } }
    @keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-10px); } }
    @keyframes shimmer { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
    </style>
    """
    st.markdown(intro_html, unsafe_allow_html=True)
    time.sleep(3)
    st.session_state.intro_complete = True
    st.rerun()

def show_login_page():
    theme = theme_engine.get_theme(st.session_state.theme)

    st.markdown(theme_engine.generate_css(st.session_state.theme, st.session_state.text_size, st.session_state.animation_enabled), unsafe_allow_html=True)

    st.markdown(f"""
    <style>
    .login-wrapper {{
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 85vh;
        padding: 20px;
        animation: fadeIn 1s ease-out;
    }}
    .login-box {{
        background: {theme['card_bg']};
        border-radius: 24px;
        padding: 50px;
        width: 100%;
        max-width: 450px;
        box-shadow: 0 25px 80px rgba(0,0,0,0.6);
        border: 2px solid {theme['border']};
        animation: scaleIn 0.6s ease-out;
        transition: all 0.3s ease;
    }}
    .login-box:hover {{
        transform: translateY(-5px);
        box-shadow: 0 30px 100px rgba(0,0,0,0.7);
    }}
    .lamp-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-bottom: 30px;
        animation: bounce 2s infinite;
    }}
    .lamp-bulb {{
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: #444;
        box-shadow: inset 0 -6px 12px rgba(0,0,0,0.6);
        transition: all 0.5s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: pulse 3s infinite;
    }}
    .lamp-bulb.lit {{
        background: {theme['accent']};
        box-shadow: 0 0 60px 20px {theme['accent']}40, 0 0 30px 10px {theme['accent']}60, inset 0 -6px 12px rgba(0,0,0,0.3);
        transform: scale(1.1);
        animation: glow 2s infinite;
    }}
    .lamp-neck {{
        width: 8px;
        height: 50px;
        background: #666;
        margin-top: -5px;
    }}
    .lamp-base {{
        width: 60px;
        height: 15px;
        background: #555;
        border-radius: 8px;
        margin-top: -5px;
    }}
    .login-title {{
        text-align: center;
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 30px;
        color: {theme['text']};
        animation: fadeIn 0.8s ease-out;
    }}
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown('<div class="login-wrapper"><div class="login-box">', unsafe_allow_html=True)

        lamp_class = "lit" if st.session_state.lamp_lit else ""
        bulb_html = f'<div class="lamp-container"><div class="lamp-bulb {lamp_class}"><div style="width: 30px; height: 30px; border-radius: 50%; background: radial-gradient(circle at 30% 30%, rgba(255,255,255,0.9), transparent); animation: rotate 10s linear infinite;"></div></div><div class="lamp-neck"></div><div class="lamp-base"></div><p style="margin-top: 10px; font-size: 12px; opacity: 0.7;">{t.get("toggle_lamp")}</p></div>'
        st.markdown(bulb_html, unsafe_allow_html=True)

        if st.button("💡 " + t.get("toggle_lamp"), key="lamp_toggle", use_container_width=True):
            st.session_state.lamp_lit = not st.session_state.lamp_lit
            st.rerun()

        if st.session_state.lamp_lit:
            title = t.get("create_account") if st.session_state.show_register else t.get("welcome_back")
            st.markdown(f'<h2 class="login-title">{title}</h2>', unsafe_allow_html=True)

            with st.form("auth_form"):
                username = st.text_input("👤 " + t.get("username"), placeholder=t.get("username"))

                student_email = None
                parent1_email = None
                parent1_phone = None
                parent2_email = None
                parent2_phone = None

                if st.session_state.show_register:
                    st.markdown("<div style='background: " + theme['secondary_bg'] + "; border-radius: 12px; padding: 15px; margin: 15px 0; border: 1px solid " + theme['border'] + ";'><div style='font-size: 16px; font-weight: 600; color: " + theme['accent'] + "; margin-bottom: 10px;'>👨‍👩‍👧 " + t.get("parental_consent") + "</div>", unsafe_allow_html=True)
                    student_email = st.text_input("📧 " + t.get("student_email"), placeholder="student@email.com")
                    parent1_email = st.text_input("👩 " + t.get("parent1_email"), placeholder="mother@email.com")
                    parent1_phone = st.text_input("📱 " + t.get("parent1_phone"), placeholder="+20 1xx xxxx xxx")
                    parent2_email = st.text_input("👨 " + t.get("parent2_email"), placeholder="father@email.com")
                    parent2_phone = st.text_input("📱 " + t.get("parent2_phone"), placeholder="+20 1xx xxxx xxx")
                    st.markdown("</div>", unsafe_allow_html=True)

                password = st.text_input("🔒 " + t.get("password"), type="password", placeholder=t.get("password"))
                confirm_password = None
                if st.session_state.show_register:
                    confirm_password = st.text_input("🔒 " + t.get("confirm_password"), type="password", placeholder=t.get("confirm_password"))

                btn_text = "🚀 " + t.get("register") if st.session_state.show_register else "🔐 " + t.get("login")
                submitted = st.form_submit_button(btn_text, use_container_width=True)

                if submitted:
                    if st.session_state.show_register:
                        if password != confirm_password:
                            st.error("❌ " + t.get("passwords_mismatch"))
                        elif len(password) < 6:
                            st.error("❌ Password must be at least 6 characters!")
                        elif not parent1_email or not parent2_email:
                            st.error("❌ " + t.get("required_field"))
                        elif username in st.session_state.users_db:
                            st.error("❌ Username already exists!")
                        else:
                            st.session_state.users_db[username] = {
                                'password': password,
                                'email': student_email,
                                'parent1_email': parent1_email,
                                'parent1_phone': parent1_phone,
                                'parent2_email': parent2_email,
                                'parent2_phone': parent2_phone,
                                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
                                'login_count': 0,
                                'subscription': 'free',
                                'focus_sessions_total': 0,
                                'focus_time_total': 0,
                                'focus_streak': 0,
                                'last_focus_date': None,
                                'focus_sessions_today': 0,
                                'focus_consent_given': False,
                                'focus_consent_declined': False,
                                'parents_notified': False
                            }
                            st.success("✅ " + t.get("account_created"))
                            st.session_state.show_register = False
                            st.rerun()
                    else:
                        if username in st.session_state.users_db and st.session_state.users_db[username]['password'] == password:
                            st.session_state.authenticated = True
                            st.session_state.current_user = username
                            st.session_state.users_db[username]['login_count'] = st.session_state.users_db[username].get('login_count', 0) + 1
                            st.session_state.users_db[username]['last_login'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                            st.session_state.subscription_tier = st.session_state.users_db[username].get('subscription', 'free')
                            st.session_state.premium_user = st.session_state.subscription_tier == 'premium'
                            st.success("✅ " + t.get("login_success"))
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ " + t.get("invalid_credentials"))

            toggle_text = t.get("have_account") if st.session_state.show_register else t.get("no_account")
            if st.button(toggle_text, type="secondary", use_container_width=True):
                st.session_state.show_register = not st.session_state.show_register
                st.rerun()
        else:
            st.markdown(f'<p style="text-align: center; opacity: 0.5; margin-top: 50px; animation: float 3s ease-in-out infinite;">{t.get("ready")}...</p>', unsafe_allow_html=True)

        st.markdown('</div></div>', unsafe_allow_html=True)

def show_sidebar():
    theme = theme_engine.get_theme(st.session_state.theme)

    with st.sidebar:
        st.markdown(f"""
        <div style="text-align: center; padding: 20px 0; animation: fadeIn 0.8s ease-out;">
            <h1 style="margin: 0; font-size: 28px; color: {theme['accent']};">🧠 Mind Vision</h1>
            <p style="margin: 5px 0; opacity: 0.7; font-size: 14px;">{t.get("app_subtitle")}</p>
            {f'<span class="premium-badge">PREMIUM</span>' if st.session_state.premium_user else f'<span style="background: {theme["border"]}; color: {theme["text"]}; padding: 4px 12px; border-radius: 20px; font-size: 12px;">FREE</span>'}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        with st.expander("⚙️ " + t.get("settings"), expanded=False):
            st.markdown(f"<div style='animation: fadeIn 0.5s ease-out;'>", unsafe_allow_html=True)

            st.subheader("🌍 " + t.get("language"))
            languages = ['English', 'العربية', 'Français', 'Español', 'Deutsch']
            current_lang_idx = languages.index(st.session_state.language) if st.session_state.language in languages else 0
            selected_language = st.selectbox(
                "",
                languages,
                index=current_lang_idx,
                key="lang_select",
                label_visibility="collapsed"
            )
            if selected_language != st.session_state.language:
                st.session_state.language = selected_language
                st.rerun()

            st.subheader("🎨 " + t.get("theme"))
            theme_names = theme_engine.get_all_themes()
            current_theme_idx = theme_names.index(st.session_state.theme) if st.session_state.theme in theme_names else 0
            selected_theme = st.selectbox(
                "",
                theme_names,
                index=current_theme_idx,
                key="theme_select",
                label_visibility="collapsed"
            )
            if selected_theme != st.session_state.theme:
                st.session_state.theme = selected_theme
                st.rerun()

            st.subheader("🔤 " + t.get("text_size"))
            sizes = ['Small', 'Medium', 'Large', 'Extra Large']
            size_map = {'Small': 'small', 'Medium': 'medium', 'Large': 'large', 'Extra Large': 'extra_large'}
            current_size_idx = list(size_map.values()).index(st.session_state.text_size) if st.session_state.text_size in size_map.values() else 1
            selected_size = st.selectbox(
                "",
                sizes,
                index=current_size_idx,
                key="size_select",
                label_visibility="collapsed"
            )
            new_size = size_map[selected_size]
            if new_size != st.session_state.text_size:
                st.session_state.text_size = new_size
                st.rerun()

            st.subheader("✨ " + t.get("animations"))
            anim_enabled = st.toggle(t.get("enable_animations"), value=st.session_state.animation_enabled)
            if anim_enabled != st.session_state.animation_enabled:
                st.session_state.animation_enabled = anim_enabled
                st.rerun()

            st.subheader("👤 " + t.get("user_info"))
            if st.button("ℹ️ " + t.get("user_info"), use_container_width=True, key="user_info_btn"):
                st.session_state.show_user_info = not st.session_state.show_user_info
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

        if st.button("📱 " + t.get("app_info"), use_container_width=True, key="app_info_btn"):
            st.session_state.show_app_info = not st.session_state.show_app_info
            st.rerun()

        if st.session_state.show_user_info:
            st.markdown("---")
            st.markdown(f"""
            <div style="background: {theme['card_bg']}; border-radius: 16px; padding: 20px; border: 2px solid {theme['accent']}; animation: scaleIn 0.4s ease-out;">
                <h3 style="margin-top: 0;">👤 {t.get("user_info")}</h3>
            """, unsafe_allow_html=True)
            if st.session_state.current_user:
                user_data = st.session_state.users_db[st.session_state.current_user]
                st.markdown(f"""
                <p><strong>{t.get('username')}:</strong> {st.session_state.current_user}</p>
                <p><strong>{t.get('email')}:</strong> {user_data.get('email', 'N/A')}</p>
                <p><strong>{t.get('member_since')}:</strong> {user_data.get('created_at', 'N/A')}</p>
                <p><strong>{t.get('total_logins')}:</strong> {user_data.get('login_count', 0)}</p>
                <p><strong>{t.get('last_login')}:</strong> {user_data.get('last_login', 'N/A')}</p>
                <p><strong>{t.get('subscription')}:</strong> {'⭐ PREMIUM' if user_data.get('subscription') == 'premium' else '🆓 FREE'}</p>
                <p><strong>{t.get('total_sessions')}:</strong> {user_data.get('focus_sessions_total', 0)}</p>
                <p><strong>{t.get('total_focus_time')}:</strong> {user_data.get('focus_time_total', 0)} min</p>
                <hr style='border-color: {theme['border']}; margin: 10px 0;'>
                <p style='color: {theme['accent']}; font-weight: bold;'>👨‍👩‍👧 Parent Information</p>
                <p><strong>{t.get('parent1_email')}:</strong> {user_data.get('parent1_email', 'N/A')}</p>
                <p><strong>{t.get('parent2_email')}:</strong> {user_data.get('parent2_email', 'N/A')}</p>
                <p><strong>{t.get('parent1_phone')}:</strong> {user_data.get('parent1_phone', 'N/A')}</p>
                <p><strong>{t.get('parent2_phone')}:</strong> {user_data.get('parent2_phone', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
            if st.button(t.get("close"), key="close_user_info"):
                st.session_state.show_user_info = False
                st.rerun()

        if st.session_state.show_app_info:
            st.markdown("---")
            st.markdown(f"""
            <div style="background: {theme['card_bg']}; border-radius: 16px; padding: 20px; border: 2px solid {theme['accent']}; animation: scaleIn 0.4s ease-out;">
                <h3 style="margin-top: 0;">📱 {t.get("app_info")}</h3>
                <p><strong>{t.get('app_title')} AI Assistant</strong></p>
                <p><strong>{t.get('version')}:</strong> 3.0 Premium</p>
                <p><strong>{t.get('developed_by')}:</strong> Mind Vision Team</p>
                <p><strong>{t.get('features')}:</strong></p>
                <ul>
                    <li>🎨 55+ Premium Themes</li>
                    <li>🌍 5 Language Support</li>
                    <li>🤖 AI Q&A & Quizzes</li>
                    <li>🧪 Interactive Periodic Table</li>
                    <li>🎨 AI Image Generation</li>
                    <li>🎯 Focus Mode with Pomodoro</li>
                    <li>📹 Camera Study Monitoring</li>
                    <li>📊 Advanced Statistics</li>
                    <li>📅 Smart Study Planner</li>
                    <li>💼 Career Explorer</li>
                    <li>🧠 AI Mind Maps</li>
                </ul>
                <p style="font-size: 12px; opacity: 0.7;">Made with ❤️ for students worldwide</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(t.get("close"), key="close_app_info"):
                st.session_state.show_app_info = False
                st.rerun()

        st.markdown("---")

        if st.button("🚪 " + t.get("logout"), use_container_width=True, key="logout_btn"):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.session_state.premium_user = False
            st.rerun()

        st.caption(f"📚 Mind Vision v3.0 • © 2026")

def check_premium_access(feature_name="this feature"):
    if not st.session_state.premium_user:
        theme = theme_engine.get_theme(st.session_state.theme)
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {theme['card_bg']}, {theme['secondary_bg']}); border: 2px solid #ffd700; border-radius: 20px; padding: 30px; text-align: center; animation: scaleIn 0.5s ease-out;">
            <div style="font-size: 48px; margin-bottom: 10px;">⭐</div>
            <h2 style="color: #ffd700; margin: 0;">{t.get("premium_feature")}</h2>
            <p style="font-size: 16px; margin: 15px 0;">{t.get("unlock_premium")}</p>
            <div style="background: {theme['bg']}; border-radius: 12px; padding: 15px; margin: 15px 0; text-align: left;">
                <p style="margin: 5px 0;">✅ {t.get("premium_tier_benefits")}</p>
                <p style="margin: 5px 0;">📊 {t.get("focus_stats")}</p>
                <p style="margin: 5px 0;">🎨 {t.get("theme")} ({len(theme_engine.get_all_themes())}+)</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("⭐ " + t.get("subscribe_now"), type="primary", use_container_width=True):
            st.info("💳 Payment integration needed. See instructions below for Egyptian payment APIs.")
        return False
    return True

def check_daily_focus_limit():
    if st.session_state.premium_user:
        return True

    today = datetime.now().strftime("%Y-%m-%d")
    user = st.session_state.users_db.get(st.session_state.current_user, {})
    last_date = user.get('last_focus_date')
    
    if last_date != today:
        user['focus_sessions_today'] = 0
        user['last_focus_date'] = today
        st.session_state.users_db[st.session_state.current_user] = user

    if user.get('focus_sessions_today', 0) >= 1:
        return False
    return True

def get_remaining_sessions():
    if st.session_state.premium_user:
        return "∞"
    user = st.session_state.users_db.get(st.session_state.current_user, {})
    today = datetime.now().strftime("%Y-%m-%d")
    if user.get('last_focus_date') != today:
        return 1
    return max(0, 1 - user.get('focus_sessions_today', 0))

def show_consent_wizard():
    theme = theme_engine.get_theme(st.session_state.theme)
    step = st.session_state.focus_consent_step
    user_data = st.session_state.users_db.get(st.session_state.current_user, {})

    st.markdown(f"<style>.consent-container {{ background: {theme['card_bg']}; border-radius: 24px; padding: 40px; border: 3px solid {theme['accent']}; margin: 20px 0; animation: fadeIn 0.6s ease-out; }}.consent-message {{ background: {theme['secondary_bg']}; border-radius: 16px; padding: 30px; margin: 20px 0; border: 2px solid {theme['border']}; font-size: 18px; line-height: 1.6; text-align: center; animation: scaleIn 0.5s ease-out; }}.consent-icon {{ font-size: 48px; margin-bottom: 15px; animation: bounce 2s infinite; }}.step-indicator {{ display: flex; justify-content: center; gap: 10px; margin-bottom: 30px; }}.step-dot {{ width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; transition: all 0.3s ease; }}.step-dot.active {{ background: {theme['accent']}; color: {theme['bg']}; transform: scale(1.2); }}.step-dot.inactive {{ background: {theme['border']}; color: {theme['text']}; }}</style>", unsafe_allow_html=True)

    st.markdown('<div class="consent-container">', unsafe_allow_html=True)
    st.markdown(f'<h2 style="text-align: center; color: {theme["accent"]};">🔒 ' + t.get("parental_consent") + '</h2>', unsafe_allow_html=True)

    dots_html = '<div class="step-indicator">'
    for i in range(3):
        cls = "active" if i == step else "inactive"
        dots_html += f'<div class="step-dot {cls}">{i+1}</div>'
    dots_html += '</div>'
    st.markdown(dots_html, unsafe_allow_html=True)

    st.markdown(f'<p style="text-align: center; opacity: 0.7; margin-bottom: 20px;">' + t.get("consent_step") + ' ' + str(step+1) + ' ' + t.get("of") + ' 3</p>', unsafe_allow_html=True)

    messages = [("📹", t.get("consent_message_1")), ("📚", t.get("consent_message_2")), ("👨‍👩‍👧", t.get("consent_message_3"))]
    icon, message = messages[step]
    st.markdown(f'<div class="consent-message"><div class="consent-icon">{icon}</div><p>{message}</p></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ " + t.get("i_accept"), use_container_width=True, type="primary"):
            if step < 2:
                st.session_state.focus_consent_step = step + 1
                st.rerun()
            else:
                st.session_state.users_db[st.session_state.current_user]['focus_consent_given'] = True
                st.session_state.users_db[st.session_state.current_user]['focus_consent_declined'] = False
                st.success("🎉 " + t.get("all_consents_accepted"))
                time.sleep(2)
                st.rerun()

    with c2:
        if st.button("❌ " + t.get("i_decline"), use_container_width=True, type="secondary"):
            st.session_state.users_db[st.session_state.current_user]['focus_consent_given'] = False
            st.session_state.users_db[st.session_state.current_user]['focus_consent_declined'] = True

            p1_email = user_data.get('parent1_email', '')
            p2_email = user_data.get('parent2_email', '')
            student_name = st.session_state.current_user

            if p1_email or p2_email:
                with st.spinner("📧 Notifying parents..."):
                    success = parent_notifier.notify_parents_focus_declined(
                        student_name=student_name,
                        parent1_email=p1_email,
                        parent2_email=p2_email,
                        sender_email=EMAIL_CONFIG['sender_email'],
                        sender_password=EMAIL_CONFIG['sender_password']
                    )
                    if success:
                        st.session_state.users_db[st.session_state.current_user]['parents_notified'] = True
                        st.error("❌ " + t.get("consent_required"))
                        st.warning("📧 " + t.get("parents_notified"))
                    else:
                        st.error("Failed to send email notifications. Please check email configuration.")
            else:
                st.error("❌ " + t.get("consent_required"))
                st.info("Parent emails not configured.")
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

def show_focus_mode():
    st.title("🎯 " + t.get("focus_mode"))
    theme = theme_engine.get_theme(st.session_state.theme)
    user_data = st.session_state.users_db.get(st.session_state.current_user, {})

    check_and_reset_daily_trials()

    if st.session_state.premium_user:
        st.markdown('<span class="premium-badge">⭐ PREMIUM ACTIVE</span>', unsafe_allow_html=True)
    else:
        remaining = get_remaining_sessions()
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.info(f"🆓 {t.get('free_tier_limit')}")
        with col_info2:
            if remaining == 0:
                st.error(f"⛔ {t.get('session_used')}")
            else:
                st.success(f"✅ {t.get('sessions_remaining')}: {remaining}")

    if user_data.get('focus_consent_declined', False) and not user_data.get('focus_consent_given', False):
        st.warning("⚠️ " + t.get("consent_required"))
        if user_data.get('parents_notified', False):
            st.info("📧 " + t.get("parents_notified"))
        if st.button("🔄 Retry Consent", use_container_width=True, type="primary"):
            st.session_state.focus_consent_step = 0
            st.session_state.focus_consent_declined = False
            st.session_state.users_db[st.session_state.current_user]['focus_consent_declined'] = False
            st.rerun()
        return

    if not user_data.get('focus_consent_given', False):
        show_consent_wizard()
        return

    if not check_daily_focus_limit() and not st.session_state.premium_user:
        st.warning(t.get("daily_limit_reached"))
        check_premium_access("unlimited focus sessions")
        return

    st.markdown(f"""
    <style>
    .focus-container {{
        background: {theme['card_bg']};
        border-radius: 24px;
        padding: 40px;
        border: 3px solid {theme['accent']};
        margin: 20px 0;
        box-shadow: 0 10px 40px {theme['accent']}20;
        animation: fadeIn 0.6s ease-out;
    }}
    .timer-display {{
        font-size: 96px;
        font-weight: bold;
        text-align: center;
        color: {theme['accent']};
        font-family: 'Courier New', monospace;
        text-shadow: 0 0 30px {theme['accent']}60;
        margin: 30px 0;
        animation: glow 2s infinite;
    }}
    .focus-status {{
        text-align: center;
        font-size: 28px;
        margin-bottom: 20px;
        color: {theme['text']};
        font-weight: 600;
        animation: fadeIn 0.5s ease-out;
    }}
    .stats-card {{
        background: {theme['secondary_bg']};
        border-radius: 16px;
        padding: 20px;
        margin: 10px 0;
        border: 1px solid {theme['border']};
        text-align: center;
        transition: all 0.3s ease;
    }}
    .stats-card:hover {{
        transform: translateY(-5px);
        border-color: {theme['accent']};
    }}
    .stats-number {{
        font-size: 36px;
        font-weight: bold;
        color: {theme['accent']};
    }}
    .stats-label {{
        font-size: 14px;
        color: {theme['text']};
        opacity: 0.7;
    }}
    .limit-badge {{
        display: inline-block;
        background: {theme['error']};
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
        margin: 10px 0;
    }}
    .limit-ok {{
        display: inline-block;
        background: {theme['success']};
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
        margin: 10px 0;
    }}
    </style>
    """, unsafe_allow_html=True)

    technique_options = {
        'pomodoro': {'study': 25, 'break': 5, 'desc': t.get('pomodoro_desc')},
        'deep_focus': {'study': 90, 'break': 20, 'desc': t.get('deep_focus_desc')},
        'full_hour': {'study': 50, 'break': 10, 'desc': t.get('full_hour_desc')}
    }
    
    selected_technique = st.selectbox(
        t.get('study_technique'),
        list(technique_options.keys()),
        format_func=lambda x: t.get(x)
    )
    
    if selected_technique:
        st.info(f"💡 {t.get('technique_tip')}: {technique_options[selected_technique]['desc']}")
        st.session_state.focus_duration = technique_options[selected_technique]['study']
        st.session_state.focus_break_duration = technique_options[selected_technique]['break']

    col1, col2, col3 = st.columns(3)
    with col1:
        focus_duration = st.number_input(
            t.get("focus_duration"), 
            min_value=1, 
            max_value=120, 
            value=st.session_state.focus_duration,
            key="focus_duration_input"
        )
    with col2:
        break_duration = st.number_input(
            t.get("break_duration"), 
            min_value=1, 
            max_value=30, 
            value=st.session_state.focus_break_duration,
            key="break_duration_input"
        )
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        camera_option = False
        if st.session_state.premium_user:
            camera_option = st.toggle(t.get("enable_camera"), value=st.session_state.camera_active)
            st.session_state.camera_active = camera_option
        else:
            st.markdown(f"<div style='opacity: 0.5; padding: 8px; background: {theme['card_bg']}; border-radius: 8px; font-size: 12px;'>📹 {t.get('premium_feature')}</div>", unsafe_allow_html=True)

    st.session_state.focus_duration = focus_duration
    st.session_state.focus_break_duration = break_duration

    with st.container():
        st.markdown('<div class="focus-container">', unsafe_allow_html=True)

        if st.session_state.focus_mode_active:
            elapsed = time.time() - st.session_state.focus_mode_start_time
            remaining = max(0, st.session_state.focus_duration * 60 - elapsed)
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            timer_text = f"{minutes:02d}:{seconds:02d}"

            if remaining > 0:
                status_text = "🔴 " + t.get("focusing")
                progress = 1 - (remaining / (st.session_state.focus_duration * 60))
                st.progress(progress, text=status_text)
            else:
                status_text = "🟢 " + t.get("break_time")
                st.balloons()
                st.success(status_text)
        else:
            timer_text = f"{st.session_state.focus_duration:02d}:00"
            status_text = "⏸️ " + t.get("ready")
            st.info(status_text)

        st.markdown(f'<div class="timer-display">{timer_text}</div>', unsafe_allow_html=True)

        if not st.session_state.premium_user:
            user = st.session_state.users_db.get(st.session_state.current_user, {})
            today = datetime.now().strftime("%Y-%m-%d")
            sessions_today = user.get('focus_sessions_today', 0) if user.get('last_focus_date') == today else 0
            
            if sessions_today >= 1 and not st.session_state.focus_mode_active:
                st.markdown(f'<div class="limit-badge">⛔ {t.get("daily_limit_reached")}</div>', unsafe_allow_html=True)
            elif not st.session_state.focus_mode_active:
                st.markdown(f'<div class="limit-ok">✅ 1 {t.get("free_tier_limit").split(":")[1].strip()}</div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            if not st.session_state.focus_mode_active:
                if st.button("▶️ " + t.get("start_focus"), use_container_width=True, type="primary"):
                    if not st.session_state.premium_user:
                        user = st.session_state.users_db.get(st.session_state.current_user, {})
                        today = datetime.now().strftime("%Y-%m-%d")
                        if user.get('last_focus_date') != today:
                            user['focus_sessions_today'] = 0
                            user['last_focus_date'] = today
                        if user.get('focus_sessions_today', 0) >= 1:
                            st.error(t.get("daily_limit_reached"))
                            return
                        user['focus_sessions_today'] = user.get('focus_sessions_today', 0) + 1
                        st.session_state.users_db[st.session_state.current_user] = user
                    st.session_state.focus_mode_active = True
                    st.session_state.focus_mode_start_time = time.time()
                    st.rerun()
        with c2:
            if st.button("⏹️ " + t.get("stop_focus"), use_container_width=True):
                if st.session_state.focus_mode_active and st.session_state.current_user:
                    elapsed = time.time() - st.session_state.focus_mode_start_time
                    minutes_focused = int(elapsed / 60)
                    user_data = st.session_state.users_db[st.session_state.current_user]
                    user_data['focus_time_total'] = user_data.get('focus_time_total', 0) + minutes_focused
                    user_data['focus_sessions_total'] = user_data.get('focus_sessions_total', 0) + 1
                st.session_state.focus_mode_active = False
                st.session_state.focus_mode_start_time = None
                st.rerun()
        with c3:
            if st.button("🔄 " + t.get("reset_focus"), use_container_width=True):
                st.session_state.focus_mode_active = False
                st.session_state.focus_mode_start_time = None
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.camera_active and st.session_state.premium_user and st.session_state.focus_mode_active:
        st.markdown("---")
        st.subheader("📹 " + t.get("enable_camera"))

        if WEBRTC_AVAILABLE:
            try:
                rtc_configuration = RTCConfiguration(
                    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
                )
                webrtc_streamer(
                    key="focus-camera",
                    mode=WebRtcMode.SENDRECV,
                    rtc_configuration=rtc_configuration,
                    video_frame_callback=None,
                    audio_frame_callback=None,
                    async_processing=True
                )
                st.info("💡 " + t.get("enable_camera"))
            except Exception as e:
                st.error(f"Camera error: {str(e)}")
        else:
            st.warning("streamlit-webrtc not installed. Run: pip install streamlit-webrtc")

    if st.session_state.premium_user and st.session_state.current_user:
        st.markdown("---")
        st.subheader("📊 " + t.get("focus_stats"))
        user_data = st.session_state.users_db[st.session_state.current_user]

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="stats-card">
                <div class="stats-number">{user_data.get('focus_sessions_total', 0)}</div>
                <div class="stats-label">{t.get('total_sessions')}</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="stats-card">
                <div class="stats-number">{user_data.get('focus_time_total', 0)}m</div>
                <div class="stats-label">{t.get('total_focus_time')}</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            total = user_data.get('focus_sessions_total', 0)
            time_total = user_data.get('focus_time_total', 0)
            avg = time_total // total if total > 0 else 0
            st.markdown(f"""
            <div class="stats-card">
                <div class="stats-number">{avg}m</div>
                <div class="stats-label">{t.get('avg_session')}</div>
            </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="stats-card">
                <div class="stats-number">{user_data.get('focus_streak', 0)}🔥</div>
                <div class="stats-label">{t.get('current_streak')}</div>
            </div>
            """, unsafe_allow_html=True)

    with st.expander("📚 " + t.get("features")):
        st.markdown("""
        ### Pomodoro Technique
        1. **Choose a task** you want to accomplish
        2. **Set the timer** for 25 minutes
        3. **Work on the task** until the timer rings
        4. **Take a short break** (5 minutes)
        5. **Repeat** and take a longer break after 4 cycles

        ### Premium Benefits
        - Unlimited daily focus sessions
        - Camera monitoring for accountability
        - Advanced statistics & streak tracking
        - Custom focus durations
        - Session history
        """)

def show_qa_section():
    st.title('📚 ' + t.get("qa"))

    subjects_options = ['Biology', 'Physics', 'Math', 'Chemistry', 'Languages', 'Art', 'Social Science', 'Computer Science', 'Entrepreneurship']
    details_options = ['Brief', 'Medium', 'Detailed']
    tone_options = ['Friendly', 'Professional', 'Simplified']
    edu_level_options = ['Primary', 'Preparatory', 'Secondary', 'College']

    col1, col2 = st.columns(2)
    with col1:
        subject = st.selectbox('📖 ' + t.get("choose_subject"), subjects_options)
        tone = st.selectbox('🗣️ ' + t.get("choose_tone"), tone_options)
    with col2:
        details = st.selectbox('📊 ' + t.get("choose_details"), details_options)
        edu_level = st.selectbox('🎓 ' + t.get("choose_edu_level"), edu_level_options)

    st.markdown("---")

    user_input = st.radio(t.get("enter_question") + ':', ['📝 ' + t.get("text"), '🎙️ ' + t.get("voice")], horizontal=True)

    question = ""
    if user_input == '📝 ' + t.get("text"):
        question = st.text_area(t.get("enter_question") + ':', height=150, placeholder=t.get("enter_question") + "...")
    elif user_input == '🎙️ ' + t.get("voice"):
        question_audio = st.audio_input(t.get("record_question") + ':')
        if question_audio:
            with st.spinner(t.get("transcribing")):
                question = convert_audio(question_audio)
            if question and not question.startswith("Error"):
                st.success(f"🎤 Transcribed: {question}")
            else:
                st.error(question)

    if st.button('✨ ' + t.get("get_answer"), key='question_btn', use_container_width=True):
        if not question:
            st.warning("⚠️ " + t.get("warning"))
        elif not ai_available:
            st.error("❌ AI service unavailable")
        else:
            prompt = f"""You are an AI studying assistant helping a {edu_level} level student with {subject}.
            Answer in a {tone} tone and provide a {details} explanation.
            The question is: {question}"""
            try:
                with st.spinner('🤖 ' + t.get("generating")):
                    response = model.generate_content(prompt)
                    st.markdown("### 📝 " + t.get("answer") + ":")
                    st.markdown(f"<div class='element-card'>{response.text}</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f'❌ {t.get("error")}: {str(e)}')

def show_quiz_section():
    st.title('🎯 ' + t.get("quizzes"))

    subjects = ['Biology', 'Physics', 'Math', 'Chemistry', 'Languages', 'Art', 'Social Science', 'Computer Science', 'Entrepreneurship']
    difficulty = ['Easy', 'Medium', 'Hard', 'Advanced']

    col1, col2 = st.columns(2)
    with col1:
        sub_option = st.selectbox('📚 ' + t.get("choose_subject"), subjects, key='quiz_subject')
    with col2:
        level = st.selectbox('⚡ ' + t.get("choose_difficulty"), difficulty)
        questions_count = st.number_input('🔢 ' + t.get("num_questions"), min_value=1, max_value=20, step=1, value=5)

    st.markdown("---")

    user_input = st.radio(t.get("enter_topic") + ':', ['📝 ' + t.get("text"), '🎙️ ' + t.get("voice")], horizontal=True, key='quiz_input')

    topic = ""
    if user_input == '📝 ' + t.get("text"):
        topic = st.text_area(t.get("enter_topic") + ':', height=150, placeholder=t.get("enter_topic") + "...")
    elif user_input == '🎙️ ' + t.get("voice"):
        topic_audio = st.audio_input(t.get("record_topic") + ':')
        if topic_audio:
            with st.spinner(t.get("transcribing")):
                topic = convert_audio(topic_audio)
            if topic and not topic.startswith("Error"):
                st.success(f"🎤 Transcribed: {topic}")
            else:
                st.error(topic)

    if st.button('🎲 ' + t.get("generate_quiz"), key='quiz_btn', use_container_width=True):
        if not topic:
            st.warning("⚠️ " + t.get("warning"))
        elif not ai_available:
            st.error("❌ AI service unavailable")
        else:
            prompt = f"""Create a quiz on the topic: {topic}
            Subject: {sub_option}
            Difficulty: {level}
            Number of questions: {questions_count}
            Format each question with:
            1. The question
            2. 4 multiple choice options (A, B, C, D)
            3. The correct answer
            4. A brief explanation"""
            try:
                with st.spinner('🎯 ' + t.get("generating")):
                    response = model.generate_content(prompt)
                    st.markdown("### 📝 " + t.get("your_quiz") + ":")
                    st.markdown(f"<div class='element-card'>{response.text}</div>", unsafe_allow_html=True)
                    
                    if st.button('📄 ' + t.get("download_pdf"), key='quiz_pdf'):
                        pdf = FPDF()
                        pdf.add_page()
                        pdf.set_font("Arial", size=12)
                        pdf.cell(200, 10, txt="Mind Vision Quiz", ln=True, align='C')
                        pdf.ln(10)
                        pdf.multi_cell(0, 10, txt=response.text)
                        pdf_output = pdf.output(dest='S').encode('latin-1')
                        st.download_button(
                            label="⬇️ " + t.get("download_pdf"),
                            data=pdf_output,
                            file_name="quiz.pdf",
                            mime="application/pdf"
                        )
            except Exception as e:
                st.error(f'❌ {t.get("error")}: {str(e)}')

def launch_periodic_table():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        periodic_table_path = os.path.join(script_dir, "scince_fair.py")

        if os.path.exists(periodic_table_path):
            if sys.platform == "win32":
                subprocess.Popen([sys.executable, periodic_table_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen([sys.executable, periodic_table_path])
        else:
            alt_paths = [
                "scince_fair.py",
                os.path.join(os.getcwd(), "scince_fair.py"),
                os.path.join(os.path.expanduser("~"), "Desktop", "scince_fair.py"),
                os.path.join(os.path.expanduser("~"), "Documents", "scince_fair.py")
            ]

            found = False
            for path in alt_paths:
                if os.path.exists(path):
                    if sys.platform == "win32":
                        subprocess.Popen([sys.executable, path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                    else:
                        subprocess.Popen([sys.executable, path])
                    found = True
                    break

            if not found:
                st.error("scince_fair.py not found.")
    except Exception as e:
        st.error(f"Error: {str(e)}")

def show_periodic_table_section():
    st.title("🧪 " + t.get("periodic_table"))

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 30px; background: #1e2542; border-radius: 20px; margin: 20px 0;">
            <h2>Open Periodic Table</h2>
            <p>Launch the complete interactive periodic table application</p>
            <ul style="text-align: left; display: inline-block;">
                <li>118 Elements with detailed properties</li>
                <li>Element merging to discover compounds</li>
                <li>Hover tooltips with quick info</li>
                <li>Category-based color coding</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔬 " + t.get("open_periodic_table"), use_container_width=True, type="primary"):
            with st.spinner(t.get("launching")):
                thread = threading.Thread(target=launch_periodic_table, daemon=True)
                thread.start()
                time.sleep(1)
                st.success("✅ " + t.get("success"))

def show_image_generation():
    st.title("🎨 " + t.get("image_gen"))

    check_and_reset_daily_trials()

    if not st.session_state.premium_user:
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"🆓 {t.get('free_tier_limit')}")
        with col2:
            if st.session_state.image_gen_used_today:
                st.error(f"⛔ {t.get('daily_trial_used')}")
            else:
                st.success(f"✅ {t.get('sessions_remaining')}: 1")

    prompt = st.text_area(t.get("describe_image") + ":", placeholder=t.get("describe_image") + "...")
    uploaded_file = st.file_uploader(t.get("upload_image_edit"), type=['png', 'jpg', 'jpeg'])

    if st.button("✨ " + t.get("generate_image"), use_container_width=True):
        if not st.session_state.premium_user and st.session_state.image_gen_used_today:
            st.warning(t.get("daily_trial_used"))
            check_premium_access("unlimited image generation")
            return

        if not prompt and not uploaded_file:
            st.warning(t.get("warning"))
            return

        with st.spinner(t.get("generating")):
            try:
                if not st.session_state.premium_user:
                    st.session_state.image_gen_used_today = True

                contents = []
                if prompt:
                    contents.append(prompt)
                if uploaded_file:
                    image = Image.open(uploaded_file)
                    contents.append(image)

                result = client.models.generate_content(
                    model="gemini-2.0-flash-exp",
                    contents=contents
                )

                for part in result.parts:
                    if part.text is not None:
                        st.markdown("### 📝 " + t.get("answer") + ":")
                        st.write(part.text)
                    elif hasattr(part, 'inline_data') and part.inline_data is not None:
                        try:
                            image_data = part.inline_data.data
                            st.markdown("### 🖼️ Generated Image:")
                            st.image(image_data)

                            st.download_button(
                                label="💾 " + t.get("download_image"),
                                data=image_data,
                                file_name="generated_image.png",
                                mime="image/png"
                            )
                        except Exception:
                            st.write("Image generated but display failed.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

def show_study_planner():
    st.title("📅 " + t.get("study_planner"))
    theme = theme_engine.get_theme(st.session_state.theme)

    subjects_list = ['Math', 'English', 'Chemistry', 'Biology', 'Physics', 'History', 'Computer Science', 'German', 'French', 'Arabic']
    
    selected_subjects = st.multiselect(t.get("select_subjects"), subjects_list)
    session_duration = st.slider(t.get("session_duration"), 15, 180, 60, step=15)
    subjects_per_day = st.number_input(t.get("subjects_per_day"), min_value=1, max_value=9, value=3)
    study_days = st.number_input(t.get("study_days"), min_value=1, max_value=7, value=5)

    if st.button("📋 " + t.get("generate_schedule"), use_container_width=True):
        if not selected_subjects:
            st.warning("⚠️ " + t.get("warning"))
            return
        
        if not ai_available:
            st.error("❌ AI service unavailable")
            return

        prompt = f"""Create a weekly study schedule with the following:
        Subjects: {', '.join(selected_subjects)}
        Session Duration: {session_duration} minutes per subject
        Subjects per day: {subjects_per_day}
        Study days per week: {study_days}
        
        Format as a markdown table with days and time slots.
        Include break times between sessions.
        Make it realistic and balanced."""
        
        try:
            with st.spinner('🤖 ' + t.get("generating")):
                response = model.generate_content(prompt)
                st.markdown("### 📅 " + t.get("your_schedule") + ":")
                st.markdown(f"<div class='element-card'>{response.text}</div>", unsafe_allow_html=True)
                
                if st.button('📄 ' + t.get("download_pdf"), key='planner_pdf'):
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    pdf.cell(200, 10, txt="Mind Vision Study Plan", ln=True, align='C')
                    pdf.ln(10)
                    pdf.multi_cell(0, 10, txt=response.text)
                    pdf_output = pdf.output(dest='S').encode('latin-1')
                    st.download_button(
                        label="⬇️ " + t.get("download_pdf"),
                        data=pdf_output,
                        file_name="study_plan.pdf",
                        mime="application/pdf"
                    )
        except Exception as e:
            st.error(f'❌ {t.get("error")}: {str(e)}')

def show_career_explorer():
    st.title("💼 " + t.get("career_explorer"))
    theme = theme_engine.get_theme(st.session_state.theme)

    career_fields = [
        t.get('medical_services'),
        t.get('marketing'),
        t.get('business_finance'),
        t.get('computer_science'),
        t.get('engineering'),
        t.get('graphic_design'),
        t.get('education'),
        t.get('law')
    ]

    col1, col2 = st.columns(2)
    with col1:
        selected_field = st.selectbox(t.get("career_field"), career_fields)
    with col2:
        question = st.text_input(t.get("career_question"), placeholder=t.get("career_question") + "...")

    if st.button("🔍 " + t.get("get_career_info"), use_container_width=True):
        if not ai_available:
            st.error("❌ AI service unavailable")
            return

        prompt = f"""Provide detailed career information about {selected_field}.
        Question: {question if question else 'General overview'}
        
        Include:
        1. Career overview and description
        2. Required education and skills
        3. Job outlook and salary ranges
        4. Daily responsibilities
        5. Growth opportunities
        6. Advice for students interested in this field"""
        
        try:
            with st.spinner('🤖 ' + t.get("generating")):
                response = model.generate_content(prompt)
                st.markdown(f"<div class='element-card'>{response.text}</div>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f'❌ {t.get("error")}: {str(e)}')

def show_mind_maps():
    st.title("🧠 " + t.get("mind_maps"))
    theme = theme_engine.get_theme(st.session_state.theme)

    check_and_reset_daily_trials()

    if not st.session_state.premium_user:
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"🆓 {t.get('free_tier_limit')}")
        with col2:
            if st.session_state.mind_map_used_today:
                st.error(f"⛔ {t.get('daily_trial_used')}")
            else:
                st.success(f"✅ {t.get('sessions_remaining')}: 1")

    topic = st.text_input(t.get("mind_map_topic"), placeholder=t.get("mind_map_topic") + "...")

    if st.button("🗺️ " + t.get("generate_mind_map"), use_container_width=True):
        if not st.session_state.premium_user and st.session_state.mind_map_used_today:
            st.warning(t.get("daily_trial_used"))
            check_premium_access("unlimited mind maps")
            return

        if not topic:
            st.warning("⚠️ " + t.get("warning"))
            return

        if not ai_available:
            st.error("❌ AI service unavailable")
            return

        if not st.session_state.premium_user:
            st.session_state.mind_map_used_today = True

        try:
            with st.spinner('🤖 ' + t.get("generating")):
                prompt = f"""Create a hierarchical mind map structure for: {topic}
                Return ONLY a JSON format with this structure:
                {{
                    "nodes": [
                        {{"id": 1, "label": "Main Topic", "level": 0}},
                        {{"id": 2, "label": "Subtopic 1", "level": 1, "parent": 1}},
                        {{"id": 3, "label": "Detail 1", "level": 2, "parent": 2}}
                    ]
                }}
                Create at least 8-10 nodes with meaningful content about {topic}."""
                
                response = model.generate_content(prompt)
                response_text = response.text
                
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    mind_map_data = json.loads(json_str)
                    
                    if PYVIS_AVAILABLE:
                        net = Network(height="600px", width="100%", bgcolor=theme['bg'], font_color=theme['text'])
                        
                        for node in mind_map_data.get('nodes', []):
                            color = '#4a9eff' if node.get('level', 0) == 0 else '#a855f7' if node.get('level', 0) == 1 else '#4ade80'
                            size = 30 if node.get('level', 0) == 0 else 20 if node.get('level', 0) == 1 else 15
                            net.add_node(node['id'], label=node['label'], color=color, size=size)
                        
                        for node in mind_map_data.get('nodes', []):
                            if 'parent' in node:
                                net.add_edge(node['parent'], node['id'])
                        
                        net.save_graph("mind_map.html")
                        with open("mind_map.html", "r", encoding='utf-8') as f:
                            html_content = f.read()
                        st.components.v1.html(html_content, height=600)
                    else:
                        st.info("PyVis not installed. Showing text-based mind map:")
                        for node in mind_map_data.get('nodes', []):
                            indent = "  " * node.get('level', 0)
                            st.write(f"{indent}• {node['label']}")
                else:
                    st.write(response_text)
        except Exception as e:
            st.error(f'❌ {t.get("error")}: {str(e)}')

def main():
    st.set_page_config(
        page_title="Mind Vision AI",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    show_language_selector()

    if not st.session_state.intro_complete:
        show_intro()
        return

    st.markdown(
        theme_engine.generate_css(
            st.session_state.theme, 
            st.session_state.text_size, 
            st.session_state.animation_enabled
        ), 
        unsafe_allow_html=True
    )

    if not st.session_state.authenticated:
        show_login_page()
        return

    show_sidebar()

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "❓ " + t.get("qa"), 
        "📑 " + t.get("quizzes"), 
        "🧪 " + t.get("periodic_table"), 
        "🎨 " + t.get("image_gen"),
        "📅 " + t.get("study_planner"),
        "💼 " + t.get("career_explorer"),
        "🧠 " + t.get("mind_maps"),
        "🎯 " + t.get("focus_mode")
    ])

    with tab1:
        show_qa_section()

    with tab2:
        show_quiz_section()

    with tab3:
        show_periodic_table_section()

    with tab4:
        show_image_generation()

    with tab5:
        show_study_planner()

    with tab6:
        show_career_explorer()

    with tab7:
        show_mind_maps()

    with tab8:
        show_focus_mode()

    st.markdown("---")
    theme = theme_engine.get_theme(st.session_state.theme)
    st.markdown(f"""
    <div style="text-align: center; padding: 30px; color: {theme['text']}; opacity: 0.8; animation: fadeIn 1s ease-out;">
        <p style="font-size: 18px; margin-bottom: 10px;">🧠 Mind Vision AI Assistant v3.0</p>
        <p style="font-size: 14px; margin-bottom: 5px;">🎨 {len(theme_engine.get_all_themes())} Premium Themes | 🌍 5 Languages | ⭐ Premium Features</p>
        <p style="font-size: 12px; opacity: 0.6;">Made with ❤️ for students worldwide • © 2026 Mind Vision</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()