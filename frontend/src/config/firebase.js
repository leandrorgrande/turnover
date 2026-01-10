import { initializeApp } from 'firebase/app'
import { getAuth } from 'firebase/auth'
import { getFirestore } from 'firebase/firestore'

const firebaseConfig = {
  apiKey: "AIzaSyBqXhZzQKvQvXzQvXzQvXzQvXzQvXzQvXzQ",
  authDomain: "lrgtechanalytics.firebaseapp.com",
  projectId: "lrgtechanalytics",
  storageBucket: "lrgtechanalytics.appspot.com",
  messagingSenderId: "286602273391",
  appId: "1:286602273391:web:xxxxxxxxxxxxxxxxxxxxx"
}

const app = initializeApp(firebaseConfig)
export const auth = getAuth(app)
export const db = getFirestore(app)
export default app
