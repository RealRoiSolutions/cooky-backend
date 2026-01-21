import React, { useEffect, useState } from 'react';
import { getShoppingList, addShoppingListItem, deleteShoppingListItem, updateShoppingListItem, addPantryItem } from '../services/api';
import IngredientSearchModal from './IngredientSearchModal';
import { Trash2, Loader, Plus, ShoppingCart, Check, Square, CheckSquare, Filter, ChefHat, Calendar, X } from 'lucide-react';

export default function ShoppingListView() {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [onlyPending, setOnlyPending] = useState(false);

    // Add to pantry modal state
    const [pantryModalOpen, setPantryModalOpen] = useState(false);
    const [itemToAddToPantry, setItemToAddToPantry] = useState(null);
    const [pantryForm, setPantryForm] = useState({ quantity: '', unit: '', expires_at: '' });
    const [addingToPantry, setAddingToPantry] = useState(false);

    // Toast notification
    const [toast, setToast] = useState(null);

    const fetchShoppingList = async () => {
        try {
            const params = onlyPending ? { only_pending: true } : {};
            const res = await getShoppingList(params);
            setItems(res.data);
        } catch (error) {
            console.error("Error fetching shopping list:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        setLoading(true);
        fetchShoppingList();
    }, [onlyPending]);

    const showToast = (message, type = 'success') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 3000);
    };

    const handleAdd = async (data) => {
        try {
            await addShoppingListItem(data);
            fetchShoppingList();
        } catch (error) {
            alert("Error al añadir a la lista");
        }
    };

    const handleDelete = async (id) => {
        if (!confirm("¿Eliminar este artículo?")) return;
        try {
            await deleteShoppingListItem(id);
            setItems(prev => prev.filter(i => i.id !== id));
        } catch (error) {
            alert("Error al eliminar");
        }
    };

    const handleToggleDone = async (item) => {
        const newDoneState = !item.is_done;

        try {
            await updateShoppingListItem(item.id, { is_done: newDoneState });
            // Optimistic update
            setItems(prev =>
                prev.map(i => i.id === item.id ? { ...i, is_done: newDoneState } : i)
            );

            // If marking as done, offer to add to pantry
            if (newDoneState) {
                setItemToAddToPantry(item);
                setPantryForm({
                    quantity: item.quantity || 1,
                    unit: item.unit || '',
                    expires_at: ''
                });
                setPantryModalOpen(true);
            }
        } catch (error) {
            alert("Error al actualizar");
        }
    };

    const closePantryModal = () => {
        setPantryModalOpen(false);
        setItemToAddToPantry(null);
        setPantryForm({ quantity: '', unit: '', expires_at: '' });
    };

    const handleAddToPantryConfirm = async () => {
        if (!itemToAddToPantry) return;
        setAddingToPantry(true);

        try {
            const data = {
                ingredient_id: itemToAddToPantry.ingredient_id,
                quantity: parseFloat(pantryForm.quantity),
                unit: pantryForm.unit
            };

            if (pantryForm.expires_at) {
                data.expires_at = new Date(pantryForm.expires_at).toISOString();
            }

            await addPantryItem(data);
            showToast('Añadido a la despensa');
            closePantryModal();
        } catch (error) {
            if (error.response?.status === 400) {
                showToast('Ya existe en la despensa', 'error');
            } else {
                showToast('Error al añadir a la despensa', 'error');
            }
        } finally {
            setAddingToPantry(false);
        }
    };

    const handleSkipAddToPantry = () => {
        closePantryModal();
    };

    return (
        <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
            {/* Toast Notification */}
            {toast && (
                <div className={`fixed top-20 left-1/2 -translate-x-1/2 z-50 px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 ${toast.type === 'success' ? 'bg-emerald-500 text-white' : 'bg-red-500 text-white'
                    }`}>
                    <ChefHat size={18} />
                    <span className="font-medium">{toast.message}</span>
                </div>
            )}

            {/* Navbar */}
            <nav className="bg-white shadow-sm border-b border-slate-100 sticky top-0 z-10">
                <div className="max-w-3xl mx-auto px-4 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="bg-emerald-500 p-2 rounded-lg text-white">
                            <ShoppingCart size={20} />
                        </div>
                        <h1 className="font-bold text-xl tracking-tight">Cooky<span className="text-emerald-500">Lista</span></h1>
                    </div>
                    <button
                        onClick={() => setIsModalOpen(true)}
                        className="bg-slate-900 hover:bg-slate-800 text-white px-4 py-2 rounded-full text-sm font-medium flex items-center gap-2 transition-all shadow-lg shadow-slate-200"
                    >
                        <Plus size={16} /> Añadir
                    </button>
                </div>
            </nav>

            <main className="max-w-3xl mx-auto px-4 py-8">
                {/* Filter Toggle */}
                <div className="mb-6 flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-slate-700">Lista de la Compra</h2>
                    <button
                        onClick={() => setOnlyPending(!onlyPending)}
                        className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-all ${onlyPending
                                ? 'bg-emerald-100 text-emerald-700'
                                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                            }`}
                    >
                        <Filter size={14} />
                        {onlyPending ? 'Solo pendientes' : 'Mostrar todos'}
                    </button>
                </div>

                {loading ? (
                    <div className="flex justify-center p-10">
                        <Loader className="animate-spin text-slate-400" />
                    </div>
                ) : items.length === 0 ? (
                    <div className="text-center py-20 bg-white rounded-2xl border border-dashed border-slate-200">
                        <div className="bg-slate-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                            <ShoppingCart className="text-slate-300" size={32} />
                        </div>
                        <h3 className="text-lg font-semibold text-slate-700">
                            {onlyPending ? 'No hay artículos pendientes' : 'Tu lista está vacía'}
                        </h3>
                        <p className="text-slate-500 mb-6 max-w-xs mx-auto">
                            {onlyPending
                                ? '¡Buen trabajo! Has comprado todo.'
                                : 'Añade ingredientes para empezar tu lista de la compra.'}
                        </p>
                        {!onlyPending && (
                            <button
                                onClick={() => setIsModalOpen(true)}
                                className="text-emerald-600 font-medium hover:underline"
                            >
                                Añadir primer artículo
                            </button>
                        )}
                    </div>
                ) : (
                    <div className="grid gap-3">
                        {items.map(item => (
                            <div
                                key={item.id}
                                className={`bg-white p-4 rounded-xl border shadow-sm flex items-center justify-between group transition-all ${item.is_done
                                        ? 'border-emerald-200 bg-emerald-50/50'
                                        : 'border-slate-100 hover:border-emerald-100'
                                    }`}
                            >
                                {/* Checkbox + Content */}
                                <div className="flex items-center gap-4">
                                    <button
                                        onClick={() => handleToggleDone(item)}
                                        className={`p-1 rounded-lg transition-colors ${item.is_done
                                                ? 'text-emerald-600 bg-emerald-100'
                                                : 'text-slate-400 hover:text-emerald-600 hover:bg-emerald-50'
                                            }`}
                                    >
                                        {item.is_done ? <CheckSquare size={22} /> : <Square size={22} />}
                                    </button>
                                    <div>
                                        <h3 className={`font-semibold text-lg capitalize ${item.is_done ? 'text-slate-400 line-through' : 'text-slate-800'
                                            }`}>
                                            {item.ingredient_name_es}
                                        </h3>
                                        <p className={`text-sm ${item.is_done ? 'text-slate-400' : 'text-slate-500'}`}>
                                            {item.quantity} {item.unit}
                                        </p>
                                    </div>
                                </div>

                                {/* Actions */}
                                <div className="flex items-center gap-2">
                                    {item.is_done && (
                                        <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded-full font-medium">
                                            <Check size={12} className="inline mr-1" />
                                            Comprado
                                        </span>
                                    )}
                                    <button
                                        onClick={() => handleDelete(item.id)}
                                        className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                                    >
                                        <Trash2 size={18} />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </main>

            <IngredientSearchModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onAdd={handleAdd}
                submitLabel="Añadir a la Lista"
                showExpiresAt={false}
            />

            {/* Add to Pantry Modal */}
            {pantryModalOpen && itemToAddToPantry && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-sm overflow-hidden">
                        <div className="p-6">
                            <div className="w-14 h-14 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                <ChefHat className="text-orange-600" size={28} />
                            </div>
                            <h3 className="text-lg font-bold text-center text-slate-800 mb-2">
                                ¿Añadir a la Despensa?
                            </h3>
                            <p className="text-center text-slate-500 text-sm mb-4">
                                Has comprado <strong className="text-slate-700 capitalize">{itemToAddToPantry.ingredient_name_es}</strong>
                            </p>

                            <div className="space-y-3 mb-4">
                                <div className="flex gap-3">
                                    <div className="flex-1">
                                        <label className="block text-xs font-medium text-gray-500 mb-1">Cantidad</label>
                                        <input
                                            type="number"
                                            step="0.1"
                                            className="w-full p-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-orange-500"
                                            value={pantryForm.quantity}
                                            onChange={(e) => setPantryForm({ ...pantryForm, quantity: e.target.value })}
                                        />
                                    </div>
                                    <div className="w-1/3">
                                        <label className="block text-xs font-medium text-gray-500 mb-1">Unidad</label>
                                        <input
                                            type="text"
                                            className="w-full p-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-orange-500"
                                            value={pantryForm.unit}
                                            onChange={(e) => setPantryForm({ ...pantryForm, unit: e.target.value })}
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-gray-500 mb-1 flex items-center gap-1">
                                        <Calendar size={12} />
                                        Fecha de caducidad (opcional)
                                    </label>
                                    <input
                                        type="date"
                                        className="w-full p-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-orange-500"
                                        value={pantryForm.expires_at}
                                        onChange={(e) => setPantryForm({ ...pantryForm, expires_at: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <button
                                    onClick={handleAddToPantryConfirm}
                                    disabled={addingToPantry || !pantryForm.quantity || !pantryForm.unit}
                                    className="w-full bg-orange-600 hover:bg-orange-700 disabled:bg-orange-300 text-white font-semibold py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
                                >
                                    <ChefHat size={18} />
                                    {addingToPantry ? 'Añadiendo...' : 'Sí, añadir a Despensa'}
                                </button>
                                <button
                                    onClick={handleSkipAddToPantry}
                                    disabled={addingToPantry}
                                    className="w-full bg-slate-100 hover:bg-slate-200 disabled:bg-slate-50 text-slate-700 font-medium py-3 rounded-lg transition-colors"
                                >
                                    No, solo marcar como comprado
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
