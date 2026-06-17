function flattenCategories(categories, depth = 0) {
  const result = [];
  for (const cat of categories) {
    result.push({ ...cat, depth });
    if (cat.children?.length) {
      result.push(...flattenCategories(cat.children, depth + 1));
    }
  }
  return result;
}

export default function CategorySelect({
  categories = [],
  value,
  onChange,
  placeholder = 'Оберіть категорію',
  className = '',
}) {
  const flat = flattenCategories(categories);

  return (
    <select
      value={value ?? ''}
      onChange={(e) => onChange(e.target.value ? parseInt(e.target.value) : null)}
      className={`border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none ${className}`}
    >
      {placeholder && <option value="">{placeholder}</option>}
      {flat.map((cat) => (
        <option key={cat.id} value={cat.id}>
          {'  '.repeat(cat.depth)}{cat.icon} {cat.name}
        </option>
      ))}
    </select>
  );
}
