import React, { useState, useEffect } from 'react';
import { searchIngredients } from '../services/api';
import { X, Search, Plus, Loader2, Calendar } from 'lucide-react';

export default function IngredientSearchModal({ isOpen, onClose, onAdd, submitLabel = "Add to Pantry", showExpiresAt = false }) {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [selectedIngredient, setSelectedIngredient] = useState(null);

    // Form state
    const [quantity, setQuantity] = useState('');
    const [unit, setUnit] = useState('');
    const [expiresAt, setExpiresAt] = useState('');

    // Debounced Search
    useEffect(() => {
        const delayDebounceFn = setTimeout(async () => {
            if (query.length >= 2) {
                setLoading(true);
                try {
                    const res = await searchIngredients({ q: query, limit: 10 });
                    setResults(res.data);
                } catch (error) {
                    console.error("Search failed", error);
                } finally {
                    setLoading(false);
                }
            } else {
                setResults([]);
            }
        }, 300);

        return () => clearTimeout(delayDebounceFn);
    }, [query]);

    const handleSelect = (ing) => {
        setSelectedIngredient(ing);
        setUnit(ing.category === 'liquid' ? 'ml' : 'g'); // Simple default logic
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!selectedIngredient || !quantity || !unit) return;

        const data = {
            ingredient_id: selectedIngredient.ingredient_id,
            quantity: parseFloat(quantity),
            unit: unit
        };

        if (showExpiresAt && expiresAt) {
            data.expires_at = new Date(expiresAt).toISOString();
        }

        onAdd(data);

        // Reset
        setSelectedIngredient(null);
        setQuery('');
        setQuantity('');
        setUnit('');
        setExpiresAt('');
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden">

                {/* Header */}
                <div className="flex justify-between items-center p-4 border-b border-gray-100">
                    <h2 className="text-lg font-bold text-gray-800">Añadir Ingrediente</h2>
                    <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-full">
                        <X size={20} className="text-gray-500" />
                    </button>
                </div>

                <div className="p-4">
                    {/* Step 1: Search */}
                    {!selectedIngredient ? (
                        <div className="space-y-4">
                            <div className="relative">
                                <Search className="absolute left-3 top-2.5 text-gray-400" size={18} />
                                <input
                                    type="text"
                                    placeholder="Buscar ingrediente (ej. ajo, leche)..."
                                    className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    autoFocus
                                />
                            </div>

                            <div className="h-60 overflow-y-auto space-y-1">
                                {loading ? (
                                    <div className="flex justify-center py-8 text-gray-400">
                                        <Loader2 className="animate-spin" />
                                    </div>
                                ) : results.length > 0 ? (
                                    results.map((ing) => (
                                        <div
                                            key={ing.ingredient_id}
                                            onClick={() => handleSelect(ing)}
                                            className="p-3 hover:bg-blue-50 rounded-lg cursor-pointer transition-colors flex justify-between items-center"
                                        >
                                            <div>
                                                <p className="font-medium text-gray-800">{ing.name_es}</p>
                                                {ing.category && <p className="text-xs text-gray-500 capitalize">{ing.category}</p>}
                                            </div>
                                            <Plus size={16} className="text-blue-500" />
                                        </div>
                                    ))
                                ) : (
                                    query.length >= 2 && (
                                        <p className="text-center text-gray-400 text-sm py-4">No se encontraron ingredientes.</p>
                                    )
                                )}
                            </div>
                        </div>
                    ) : (
                        /* Step 2: Details Form */
                        <form onSubmit={handleSubmit} className="space-y-4 animate-in fade-in zoom-in duration-200">
                            <div className="bg-blue-50 p-3 rounded-lg flex justify-between items-center">
                                <span className="font-semibold text-blue-800">{selectedIngredient.name_es}</span>
                                <button
                                    type="button"
                                    onClick={() => setSelectedIngredient(null)}
                                    className="text-xs text-blue-600 hover:underline"
                                >
                                    Cambiar
                                </button>
                            </div>

                            <div className="flex gap-3">
                                <div className="flex-1">
                                    <label className="block text-xs font-medium text-gray-500 mb-1">Cantidad</label>
                                    <input
                                        type="number"
                                        step="0.1"
                                        required
                                        className="w-full p-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                                        placeholder="0.0"
                                        value={quantity}
                                        onChange={(e) => setQuantity(e.target.value)}
                                    />
                                </div>
                                <div className="w-1/3">
                                    <label className="block text-xs font-medium text-gray-500 mb-1">Unidad</label>
                                    <input
                                        type="text"
                                        required
                                        className="w-full p-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                                        placeholder="g, ml..."
                                        value={unit}
                                        onChange={(e) => setUnit(e.target.value)}
                                    />
                                </div>
                            </div>

                            {showExpiresAt && (
                                <div>
                                    <label className="block text-xs font-medium text-gray-500 mb-1 flex items-center gap-1">
                                        <Calendar size={12} />
                                        Fecha de caducidad (opcional)
                                    </label>
                                    <input
                                        type="date"
                                        className="w-full p-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                                        value={expiresAt}
                                        onChange={(e) => setExpiresAt(e.target.value)}
                                    />
                                </div>
                            )}

                            <button
                                type="submit"
                                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-lg transition-colors"
                            >
                                {submitLabel}
                            </button>
                        </form>
                    )}
                </div>
            </div>
        </div>
    );
}
