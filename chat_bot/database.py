from firebase_admin import credentials, firestore, storage
import firebase_admin


cred = credentials.Certificate('XXX')
firebase_admin.initialize_app(cred, {
    'XXX'
})

db = firestore.client()
bucket = storage.bucket()