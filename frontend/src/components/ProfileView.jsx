import React, { useEffect, useState } from 'react';
import { getProfile, updateProfile } from '../services/api';
import { User, Save, Loader, Check, AlertTriangle } from 'lucide-react';

const DIET_OPTIONS = [
    { value: '', label: 'Sin restricción' },
    { value: 'omnivore', label: 'Omnívoro' },
    { value: 'vegetarian', label: 'Vegetariano' },
    { value: 'vegan', label: 'Vegano' },
    { value: 'pescatarian', label: 'Pescetariano' },
    { value: 'keto', label: 'Keto' },
    { value: 'paleo', label: 'Paleo' },
];

const INTOLERANCE_OPTIONS = [
    { value: 'gluten', label: 'Gluten' },
    { value: 'dairy', label: 'Lácteos' },
    { value: 'egg', label: 'Huevo' },
    { value: 'nut', label: 'Frutos secos' },
    { value: 'soy', label: 'Soja' },
    { value: 'shellfish', label: 'Mariscos' },
    { value: 'fish', label: 'Pescado' },
    { value: 'wheat', label: 'Trigo' },
    { value: 'sesame', label: 'Sésamo' },
];

export default function ProfileView() {
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [toast, setToast] = useState(null);

    // Form state
    const [dietType, setDietType] = useState('');
    const [intolerances, setIntolerances] = useState([]);

    const fetchProfile = async () => {
        try {
            const res = await getProfile();
            setProfile(res.data);
            setDietType(res.data.diet_type || '');
            setIntolerances(res.data.intolerances || []);
        } catch (error) {
            console.error("Error fetching profile:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchProfile();
    }, []);

    const showToast = (message, type = 'success') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 3000);
    };

    const toggleIntolerance = (value) => {
        setIntolerances(prev =>
            prev.includes(value)
                ? prev.filter(i => i !== value)
                : [...prev, value]
        );
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            await updateProfile({
                diet_type: dietType || null,
                intolerances: intolerances
            });
            showToast('Perfil guardado');
        } catch (error) {
            console.error("Error saving profile:", error);
            showToast('Error al guardar', 'error');
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
            {/* Toast */}
            {toast && (
                <div className={`fixed top-20 left-1/2 -translate-x-1/2 z-50 px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 ${toast.type === 'success' ? 'bg-emerald-500 text-white' : 'bg-red-500 text-white'
                    }`}>
                    <Check size={18} />
                    <span className="font-medium">{toast.message}</span>
                </div>
            )}

            {/* Header */}
            <nav className="bg-white shadow-sm border-b border-slate-100 sticky top-0 z-10">
                <div className="max-w-3xl mx-auto px-4 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="bg-violet-500 p-2 rounded-lg text-white">
                            <User size={20} />
                        </div>
                        <h1 className="font-bold text-xl tracking-tight">Cooky<span className="text-violet-500">Perfil</span></h1>
                    </div>
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="bg-violet-600 hover:bg-violet-700 disabled:bg-violet-300 text-white px-4 py-2 rounded-full text-sm font-medium flex items-center gap-2 transition-all"
                    >
                        {saving ? <Loader className="animate-spin" size={16} /> : <Save size={16} />}
                        Guardar
                    </button>
                </div>
            </nav>

            <main className="max-w-3xl mx-auto px-4 py-6">
                {loading ? (
                    <div className="flex justify-center py-10">
                        <Loader className="animate-spin text-slate-400" />
                    </div>
                ) : (
                    <div className="space-y-6">
                        {/* Diet Type */}
                        <div className="bg-white rounded-xl p-5 border border-slate-100 shadow-sm">
                            <h3 className="font-semibold text-slate-700 mb-4 flex items-center gap-2">
                                🥗 Tipo de Dieta
                            </h3>
                            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                                {DIET_OPTIONS.map(opt => (
                                    <button
                                        key={opt.value}
                                        onClick={() => setDietType(opt.value)}
                                        className={`p-3 rounded-lg border text-sm font-medium transition-all ${dietType === opt.value
                                                ? 'border-violet-500 bg-violet-50 text-violet-700'
                                                : 'border-slate-200 bg-white text-slate-600 hover:border-violet-200'
                                            }`}
                                    >
                                        {opt.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Intolerances */}
                        <div className="bg-white rounded-xl p-5 border border-slate-100 shadow-sm">
                            <h3 className="font-semibold text-slate-700 mb-2 flex items-center gap-2">
                                <AlertTriangle size={18} className="text-amber-500" />
                                Intolerancias y Alergias
                            </h3>
                            <p className="text-sm text-slate-500 mb-4">
                                Selecciona los alimentos que no puedes o no quieres consumir.
                            </p>
                            <div className="flex flex-wrap gap-2">
                                {INTOLERANCE_OPTIONS.map(opt => (
                                    <button
                                        key={opt.value}
                                        onClick={() => toggleIntolerance(opt.value)}
                                        className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${intolerances.includes(opt.value)
                                                ? 'bg-red-100 text-red-700 border border-red-300'
                                                : 'bg-slate-100 text-slate-600 border border-slate-200 hover:bg-slate-200'
                                            }`}
                                    >
                                        {intolerances.includes(opt.value) && '✕ '}
                                        {opt.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Info Card */}
                        <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
                            <h4 className="font-medium text-blue-800 mb-1">¿Para qué sirve?</h4>
                            <p className="text-sm text-blue-600">
                                Cooky usará tu perfil para filtrar recetas incompatibles y mostrarte avisos cuando una receta contenga ingredientes a los que eres intolerante.
                            </p>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
