# Product Expert Memory
# Purpose: This file documents the validated expert logic for identifying product categories.
# It serves as the "Source of Truth" for the `assign_ai_categories.py` script.
# Structure: Organized by Logic Section (Global, Fresh Meat, Eggs) -> Source Store.
# Content: Contains exact pseudocode conditions that must be mirrored in the implementation.

## Global Exclusions
Applies to ALL Fresh Meat categories:
```python
def is_not_fresh_meat(name, cats_str):
    bad_words = ['uzené', 'uzeny', 'uzená', 'marinovan', 'mražen', 'mrazen', 'sušené', 'sušený', 'sušene']
    txt = (name + " " + cats_str).lower()
    if any(w in txt for w in bad_words): REJECT
```

## Fresh Meat Logic

### Albert (Wolt)
```python
if 'MASO A RYBY' in cats:
    if 'HOVĚZÍ A TELECÍ' in cats: yield 'fresh-meat-beef'
    elif 'VEPŘOVÉ MASO' in cats:  yield 'fresh-meat-pork'
    elif 'DRŮBEŽ' in cats:        yield 'fresh-meat-poultry'
    elif 'MLETÉ MASO' in cats:
        # Ground meat analysis
        if 'hovězí' in name: yield 'fresh-meat-beef'
        if 'vepřové' in name: yield 'fresh-meat-pork'
        if not detected: yield 'fresh-meat-other'
```

### Billa (Wolt)
```python
if 'MASO A UZENINY' in cats:
    if 'HOVĚZÍ MASO' in cats:   yield 'fresh-meat-beef'
    elif 'VEPŘOVÉ MASO' in cats: yield 'fresh-meat-pork' 
    elif 'DRŮBEŽ' in cats:       yield 'fresh-meat-poultry'
    elif 'JINÉ MASO' in cats:    yield 'fresh-meat-other'
```

### Globus (Wolt)
```python
if 'MASO A RYBY' in cats and 'ŘEZNICTVÍ GLOBUS' in cats:
    # Generic category, check name
    if 'hovězí' in name or 'telecí' in name: yield 'fresh-meat-beef'
    elif 'vepřov' in name:                   yield 'fresh-meat-pork'
    elif 'kuřecí' or 'krůtí' or 'kachn' in name: yield 'fresh-meat-poultry'
    elif 'králí' or 'zvěřin' or 'jehněčí' in name: yield 'fresh-meat-other'
    elif 'mleté' or 'mělněné' in name:       yield 'fresh-meat-other'

elif 'Maso, drůbež, ryby' in cats:
    if 'Hovězí a telecí maso' in cats: yield 'fresh-meat-beef'
    elif 'Vepřové maso' in cats:       yield 'fresh-meat-pork'
    elif 'Drůbež' in cats:             yield 'fresh-meat-poultry'
```

### Kupi
```python
if 'Maso, uzeniny a ryby' in cats:
    if 'Hovězí maso' in cats:      yield 'fresh-meat-beef'
    elif 'Vepřové maso' in cats:   yield 'fresh-meat-pork'
    elif 'Drůbež' in cats:         yield 'fresh-meat-poultry'
    elif 'Ostatní maso' in cats:   yield 'fresh-meat-other'
    elif 'Zvěřina' in cats:        yield 'fresh-meat-other'
```

### Tesco
```python
if 'Maso, ryby a uzeniny' in cats or 'Maso a lahůdky' in cats:
    # Check specific subcategories first
    if 'Hovězí a telecí' in cats or 'Hovězí' in cats: yield 'fresh-meat-beef'
    elif 'Hovězí a telecí' in cats and 'Telecí' in name: yield 'fresh-meat-beef' # included
    elif 'Vepřové' in cats:                           yield 'fresh-meat-pork'
    elif 'Drůbež' in cats:                            yield 'fresh-meat-poultry'
    elif 'Mleté maso' in cats:                        yield 'fresh-meat-other'
    elif 'Jehněčí a králičí' in cats:                 yield 'fresh-meat-other'
    
    # Fallback for generic paths
    elif 'Maso' in cats or 'Maso, ryby a speciality' in cats:
        # Check name keywords (same as Globus fallback)
        match_name_keywords(name) 
```

## Fresh Eggs Logic ("fresh-chicken-eggs")
*Excludes: "křepelčí"*

### Albert, Globus, Billa (Wolt)
```python
# Albert/Globus: 'VEJCE A DROŽDÍ', Billa: 'VEJCE & DROŽDÍ'
if 'MLÉČNÉ A CHLAZENÉ' in cats (or similar root):
    if 'VEJCE A DROŽDÍ' in cats (or '&'):
        if 'droždí' not in name: 
            yield 'fresh-chicken-eggs'
```

### Tesco
```python
if cats[2] == 'Vejce':
    yield 'fresh-chicken-eggs'
```

### Kupi
```python
if 'Vejce' in cats or cats[1] == 'Vejce':
    yield 'fresh-chicken-eggs'
```
