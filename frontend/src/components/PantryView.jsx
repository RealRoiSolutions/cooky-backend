import React, { useEffect, useState } from 'react';
import { getPantryItems, addPantryItem, deletePantryItem, updatePantryItem, addShoppingListItem } from '../services/api';
import IngredientSearchModal from './IngredientSearchModal';
import ExpiringRecommendations from './ExpiringRecommendations';
import { Trash2, Edit2, Loader, Plus, ChefHat, CheckCircle, X, ShoppingCart, AlertTriangle, Clock } from 'lucide-react';

export default function PantryView({ onSelectRecipe }) {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);

    // Editing state
    const [editingId, setEditingId] = useState(null);
    const [editForm, setEditForm] = useState({ quantity: '', unit: '', expires_at: '' });

    // Consume confirmation modal state
    const [consumeModalOpen, setConsumeModalOpen] = useState(false);
    const [itemToConsume, setItemToConsume] = useState(null);
    const [consuming, setConsuming] = useState(false);

    // Toast notification
    const [toast, setToast] = useState(null);

    const fetchPantry = async () => {
        try {
            const res = await getPantryItems();
            setItems(res.data);
        } catch (error) {
            console.error("Error fetching pantry:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchPantry();
    }, []);

    // Expiration helpers
    const getExpirationInfo = (expiresAt) => {
        if (!expiresAt) return null;
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const expDate = new Date(expiresAt);
        expDate.setHours(0, 0, 0, 0);
        const diffTime = expDate - today;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        if (diffDays < 0) {
            return { status: 'expired', days: Math.abs(diffDays), label: `CADUCADO hace ${Math.abs(diffDays)} día(s)` };
        } else if (diffDays === 0) {
            return { status: 'today', days: 0, label: 'CADUCA HOY' };
        } else if (diffDays <= 7) {
            return { status: 'soon', days: diffDays, label: `Caduca en ${diffDays} día(s)` };
        }
        return { status: 'ok', days: diffDays, label: `Caduca en ${diffDays} días` };
    };

    const handleAdd = async (data) => {
        try {
            await addPantryItem(data);
            fetchPantry();
        } catch (error) {
            if (error.response?.status === 400) {
                alert("Este ingrediente ya está en la despensa. Usa editar para actualizar.");
            } else {
                alert("Error al añadir el ingrediente");
            }
        }
    };

    const handleDelete = async (id) => {
        if (!confirm("¿Eliminar este ingrediente de la despensa?")) return;
        try {
            await deletePantryItem(id);
            setItems(prev => prev.filter(i => i.id !== id));
        } catch (error) {
            alert("Error al eliminar");
        }
    };

    const startEdit = (item) => {
        setEditingId(item.id);
        const expDate = item.expires_at ? new Date(item.expires_at).toISOString().split('T')[0] : '';
        setEditForm({ quantity: item.quantity, unit: item.unit, expires_at: expDate });
    };

    const cancelEdit = () => {
        setEditingId(null);
        setEditForm({ quantity: '', unit: '', expires_at: '' });
    };

    const saveEdit = async (id) => {
        try {
            const updateData = {
                quantity: parseFloat(editForm.quantity),
                unit: editForm.unit
            };
            if (editForm.expires_at) {
                updateData.expires_at = new Date(editForm.expires_at).toISOString();
            }
            await updatePantryItem(id, updateData);
            setEditingId(null);
            fetchPantry();
        } catch (error) {
            alert("Error al actualizar");
        }
    };

    // Consume flow
    const openConsumeModal = (item) => {
        setItemToConsume(item);
        setConsumeModalOpen(true);
    };

    const closeConsumeModal = () => {
        setConsumeModalOpen(false);
        setItemToConsume(null);
    };

    const showToast = (message, type = 'success') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 3000);
    };

    const handleConsumeOnly = async () => {
        if (!itemToConsume) return;
        setConsuming(true);
        try {
            await deletePantryItem(itemToConsume.id);
            setItems(prev => prev.filter(i => i.id !== itemToConsume.id));
            showToast('Ingrediente eliminado de la despensa');
            closeConsumeModal();
        } catch (error) {
            alert("Error al eliminar el ingrediente");
        } finally {
            setConsuming(false);
        }
    };

    const handleConsumeAndAddToList = async () => {
        if (!itemToConsume) return;
        setConsuming(true);
        try {
            await deletePantryItem(itemToConsume.id);
            setItems(prev => prev.filter(i => i.id !== itemToConsume.id));

            try {
                await addShoppingListItem({
                    ingredient_id: itemToConsume.ingredient_id,
                    quantity: 1.0,
                    unit: itemToConsume.unit || null
                });
                showToast('Añadido a la lista de la compra', 'success');
            } catch (listError) {
                console.error("Error adding to shopping list:", listError);
                showToast('Eliminado de despensa, pero error al añadir a lista', 'error');
            }

            closeConsumeModal();
        } catch (error) {
            alert("Error al eliminar el ingrediente");
        } finally {
            setConsuming(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
            {/* Toast Notification */}
            {toast && (
                <div className={`fixed top-20 left-1/2 -translate-x-1/2 z-50 px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 ${toast.type === 'success' ? 'bg-emerald-500 text-white' : 'bg-red-500 text-white'
                    }`}>
                    {toast.type === 'success' ? <ShoppingCart size={18} /> : <X size={18} />}
                    <span className="font-medium">{toast.message}</span>
                </div>
            )}

            {/* Navbar */}
            <nav className="bg-white shadow-sm border-b border-slate-100 sticky top-0 z-10">
                <div className="max-w-3xl mx-auto px-4 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="bg-orange-500 p-2 rounded-lg text-white">
                            <ChefHat size={20} />
                        </div>
                        <h1 className="font-bold text-xl tracking-tight">Cooky<span className="text-orange-500">Despensa</span></h1>
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
                {/* Expiring Recommendations Section */}
                {onSelectRecipe && <ExpiringRecommendations onSelectRecipe={onSelectRecipe} limit={3} />}

                {loading ? (
                    <div className="flex justify-center p-10">
                        <Loader className="animate-spin text-slate-400" />
                    </div>
                ) : items.length === 0 ? (
                    <div className="text-center py-20 bg-white rounded-2xl border border-dashed border-slate-200">
                        <div className="bg-slate-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                            <ChefHat className="text-slate-300" size={32} />
                        </div>
                        <h3 className="text-lg font-semibold text-slate-700">Tu despensa está vacía</h3>
                        <p className="text-slate-500 mb-6 max-w-xs mx-auto">Añade ingredientes para ver qué puedes cocinar</p>
                        <button
                            onClick={() => setIsModalOpen(true)}
                            className="text-orange-600 font-medium hover:underline"
                        >
                            Añadir primer ingrediente
                        </button>
                    </div>
                ) : (
                    <div className="grid gap-3">
                        {items.map(item => {
                            const expInfo = getExpirationInfo(item.expires_at);
                            return (
                                <div
                                    key={item.id}
                                    className={`bg-white p-4 rounded-xl border shadow-sm flex items-center justify-between group transition-colors ${expInfo?.status === 'expired' ? 'border-red-200 bg-red-50/30' :
                                        expInfo?.status === 'today' ? 'border-orange-200 bg-orange-50/30' :
                                            expInfo?.status === 'soon' ? 'border-amber-200 bg-amber-50/30' :
                                                'border-slate-100 hover:border-orange-100'
                                        }`}
                                >
                                    {/* Content */}
                                    {editingId === item.id ? (
                                        <div className="flex items-center gap-2 flex-1 flex-wrap">
                                            <span className="font-medium text-slate-400 w-full sm:w-auto truncate">{item.ingredient_name}</span>
                                            <input
                                                className="w-20 p-1 border rounded text-right"
                                                type="number"
                                                value={editForm.quantity}
                                                onChange={e => setEditForm({ ...editForm, quantity: e.target.value })}
                                            />
                                            <input
                                                className="w-20 p-1 border rounded"
                                                type="text"
                                                value={editForm.unit}
                                                onChange={e => setEditForm({ ...editForm, unit: e.target.value })}
                                            />
                                            <input
                                                className="w-32 p-1 border rounded text-sm"
                                                type="date"
                                                value={editForm.expires_at}
                                                onChange={e => setEditForm({ ...editForm, expires_at: e.target.value })}
                                            />
                                            <div className="flex gap-1">
                                                <button onClick={() => saveEdit(item.id)} className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">Guardar</button>
                                                <button onClick={cancelEdit} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">Cancelar</button>
                                            </div>
                                        </div>
                                    ) : (
                                        <>
                                            <div className="flex items-center gap-4">
                                                <div className="w-10 h-10 rounded-full bg-slate-50 flex items-center justify-center text-xl">
                                                    🥗
                                                </div>
                                                <div>
                                                    <h3 className="font-semibold text-slate-800 text-lg capitalize">{item.ingredient_name}</h3>
                                                    <p className="text-slate-500 text-sm">{item.quantity} {item.unit}</p>
                                                    {expInfo && (
                                                        <div className={`flex items-center gap-1 text-xs mt-1 ${expInfo.status === 'expired' ? 'text-red-600' :
                                                            expInfo.status === 'today' ? 'text-orange-600' :
                                                                expInfo.status === 'soon' ? 'text-amber-600' :
                                                                    'text-slate-400'
                                                            }`}>
                                                            {expInfo.status === 'expired' || expInfo.status === 'today' ? (
                                                                <AlertTriangle size={12} />
                                                            ) : (
                                                                <Clock size={12} />
                                                            )}
                                                            {expInfo.label}
                                                        </div>
                                                    )}
                                                </div>
                                            </div>

                                            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button
                                                    onClick={() => openConsumeModal(item)}
                                                    className="p-2 text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg"
                                                    title="Marcar como consumido"
                                                >
                                                    <CheckCircle size={18} />
                                                </button>
                                                <button
                                                    onClick={() => startEdit(item)}
                                                    className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg"
                                                    title="Editar"
                                                >
                                                    <Edit2 size={18} />
                                                </button>
                                                <button
                                                    onClick={() => handleDelete(item.id)}
                                                    className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                                                    title="Eliminar"
                                                >
                                                    <Trash2 size={18} />
                                                </button>
                                            </div>
                                        </>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}
            </main>

            <IngredientSearchModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onAdd={handleAdd}
                submitLabel="Añadir a Despensa"
                showExpiresAt={true}
            />

            {/* Consume Confirmation Modal */}
            {consumeModalOpen && itemToConsume && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-sm overflow-hidden">
                        <div className="p-6">
                            <div className="w-14 h-14 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                <CheckCircle className="text-emerald-600" size={28} />
                            </div>
                            <h3 className="text-lg font-bold text-center text-slate-800 mb-2">
                                ¿Marcar como consumido?
                            </h3>
                            <p className="text-center text-slate-500 text-sm mb-1">
                                <strong className="text-slate-700 capitalize">{itemToConsume.ingredient_name}</strong>
                            </p>
                            <p className="text-center text-slate-500 text-sm mb-6">
                                ¿Quieres añadirlo a la lista de la compra para reponerlo?
                            </p>

                            <div className="space-y-2">
                                <button
                                    onClick={handleConsumeAndAddToList}
                                    disabled={consuming}
                                    className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-300 text-white font-semibold py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
                                >
                                    <ShoppingCart size={18} />
                                    {consuming ? 'Procesando...' : 'Sí, añadir a Lista'}
                                </button>
                                <button
                                    onClick={handleConsumeOnly}
                                    disabled={consuming}
                                    className="w-full bg-slate-100 hover:bg-slate-200 disabled:bg-slate-50 text-slate-700 font-medium py-3 rounded-lg transition-colors"
                                >
                                    {consuming ? 'Procesando...' : 'No, solo eliminar'}
                                </button>
                                <button
                                    onClick={closeConsumeModal}
                                    disabled={consuming}
                                    className="w-full text-slate-500 hover:text-slate-700 font-medium py-2 transition-colors"
                                >
                                    Cancelar
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
