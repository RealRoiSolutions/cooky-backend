import React, { useEffect, useState } from 'react';
import { getDailySummary, deleteLogEntry } from '../services/api';
import { ChefHat, Calendar, Trash2, ChevronLeft, ChevronRight, Flame, Droplet, Wheat, Dumbbell } from 'lucide-react';

export default function FoodLogView() {
    const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
    const [summary, setSummary] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchSummary = async () => {
        setLoading(true);
        try {
            const res = await getDailySummary(date);
            setSummary(res.data);
        } catch (error) {
            console.error("Error fetching log summary:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSummary();
    }, [date]);

    const changeDate = (days) => {
        const currentDate = new Date(date);
        currentDate.setDate(currentDate.getDate() + days);
        setDate(currentDate.toISOString().split('T')[0]);
    };

    const handleDelete = async (id) => {
        if (!confirm("Are you sure you want to delete this entry?")) return;
        try {
            await deleteLogEntry(id);
            fetchSummary();
        } catch (error) {
            alert("Error deleting entry");
        }
    };

    // Helper for macro cards
    const MacroCard = ({ icon: Icon, label, value, unit, color }) => (
        <div className={`flex-1 bg-white p-3 rounded-xl border border-slate-100 shadow-sm flex flex-col items-center justify-center gap-1 ${color}`}>
            <Icon size={20} className="mb-1 opacity-80" />
            <span className="text-xl font-bold">{Math.round(value)}</span>
            <span className="text-xs font-medium opacity-60 uppercase">{label}</span>
        </div>
    );

    return (
        <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
            {/* Header */}
            <nav className="bg-white shadow-sm border-b border-slate-100 sticky top-0 z-10 px-4 h-16 flex items-center justify-between max-w-3xl mx-auto w-full">
                <div className="flex items-center gap-2">
                    <div className="bg-indigo-500 p-2 rounded-lg text-white">
                        <Calendar size={20} />
                    </div>
                    <h1 className="font-bold text-xl tracking-tight">Cooky<span className="text-indigo-500">Diario</span></h1>
                </div>
            </nav>

            <main className="max-w-3xl mx-auto px-4 py-6">

                {/* Date Navigation */}
                <div className="flex items-center justify-between mb-6 bg-white p-2 rounded-xl border border-slate-100 shadow-sm">
                    <button onClick={() => changeDate(-1)} className="p-2 hover:bg-slate-50 rounded-lg text-slate-500">
                        <ChevronLeft size={24} />
                    </button>
                    <div className="font-semibold text-lg flex items-center gap-2">
                        <Calendar size={18} className="text-indigo-500" />
                        {new Date(date).toLocaleDateString('es-ES', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                    </div>
                    <button onClick={() => changeDate(1)} className="p-2 hover:bg-slate-50 rounded-lg text-slate-500">
                        <ChevronRight size={24} />
                    </button>
                </div>

                {loading && !summary ? (
                    <div className="text-center py-10">Cargando...</div>
                ) : (
                    <>
                        {/* Summary Cards */}
                        <div className="grid grid-cols-4 gap-2 mb-6">
                            <MacroCard
                                icon={Flame}
                                label="Kcal"
                                value={summary?.totals?.calories || 0}
                                color="text-orange-500"
                            />
                            <MacroCard
                                icon={Dumbbell}
                                label="Prot"
                                value={summary?.totals?.protein || 0}
                                unit="g"
                                color="text-emerald-500"
                            />
                            <MacroCard
                                icon={Wheat}
                                label="Carbs"
                                value={summary?.totals?.carbs || 0}
                                unit="g"
                                color="text-amber-500"
                            />
                            <MacroCard
                                icon={Droplet}
                                label="Grasas"
                                value={summary?.totals?.fat || 0}
                                unit="g"
                                color="text-rose-500"
                            />
                        </div>

                        {/* Entries List */}
                        <div className="space-y-3">
                            <h3 className="font-semibold text-slate-700 mb-2">Comidas registradas</h3>

                            {summary?.entries?.length === 0 ? (
                                <div className="text-center py-10 bg-white rounded-2xl border border-dashed border-slate-200 text-slate-400">
                                    No hay registros para este día.
                                </div>
                            ) : (
                                summary?.entries?.map(entry => (
                                    <div key={entry.id} className="bg-white p-4 rounded-xl border border-slate-100 shadow-sm flex items-center justify-between group">
                                        <div className="flex items-center gap-3">
                                            <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg ${entry.type === 'recipe' ? 'bg-rose-50 text-rose-500' : 'bg-blue-50 text-blue-500'
                                                }`}>
                                                {entry.type === 'recipe' ? <ChefHat size={20} /> : '🥗'}
                                            </div>
                                            <div>
                                                <h4 className="font-medium text-slate-800 line-clamp-1">
                                                    {entry.type === 'recipe' ? entry.recipe_title : entry.ingredient_name_es}
                                                </h4>
                                                <div className="text-xs text-slate-500 flex gap-2">
                                                    <span>{entry.quantity} {entry.unit}</span>
                                                    <span>•</span>
                                                    <span>{Math.round(entry.macros.calories)} kcal</span>
                                                </div>
                                            </div>
                                        </div>

                                        <button
                                            onClick={() => handleDelete(entry.id)}
                                            className="p-2 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                                        >
                                            <Trash2 size={18} />
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>
                    </>
                )}
            </main>
        </div>
    );
}
