import numpy as np
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

data = ['0news - Ikke nyhetsverdig', '0news - Ikke nyhetsverdig', '0news - Nyhetsverdig', '0news - Ikke nyhetsverdig', '0news - Ikke nyhetsverdig', '0news - Ikke nyhetsverdig', '0news - Ikke nyhetsverdig', '0news - Nyhetsverdig', '0news - Ikke nyhetsverdig', '1news - Nyhetsverdig', '1news - Ikke nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '1news - Ikke nyhetsverdig', '1news - Ikke nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '2news - Ikke nyhetsverdig', '2news - Ikke nyhetsverdig', '2news - Ikke nyhetsverdig', '2news - Ikke nyhetsverdig', '2news - Ikke nyhetsverdig', '2news - Ikke nyhetsverdig', '0news - Ikke nyhetsverdig', '0news - Ikke nyhetsverdig', '0news - Nyhetsverdig', '0news - Ikke nyhetsverdig', '0news - Nyhetsverdig', '0news - Ikke nyhetsverdig', '0news - Ikke nyhetsverdig', '0news - Nyhetsverdig', '0news - Ikke nyhetsverdig', '1news - Ikke nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '1news - Ikke nyhetsverdig', '1news - Ikke nyhetsverdig', '1news - Ikke nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '1news - Ikke nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '2news - Ikke nyhetsverdig', '2news - Ikke nyhetsverdig', '2news - Nyhetsverdig', '2news - Ikke nyhetsverdig', '2news - Ikke nyhetsverdig', '2news - Ikke nyhetsverdig', '0news - Ikke nyhetsverdig', '0news - Ikke nyhetsverdig', '0news - Nyhetsverdig', '0news - Ikke nyhetsverdig', '0news - Ikke nyhetsverdig', '0news - Nyhetsverdig', '0news - Ikke nyhetsverdig', '0news - Ikke nyhetsverdig', '0news - Ikke nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '1news - Ikke nyhetsverdig', '1news - Ikke nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '1news - Nyhetsverdig', '1news - Ikke nyhetsverdig', '1news - Nyhetsverdig', '2news - Ikke nyhetsverdig', '2news - Ikke nyhetsverdig', '2news - Nyhetsverdig', '2news - Ikke nyhetsverdig', '2news - Ikke nyhetsverdig', '2news - Ikke nyhetsverdig']
data2 = ['3news - Ikke nyhetsverdig', '3news - Nyhetsverdig', '3news - Ikke nyhetsverdig', '3news - Ikke nyhetsverdig', '3news - Nyhetsverdig', '3news - Ikke nyhetsverdig', '4news - Nyhetsverdig', '4news - Ikke nyhetsverdig', '4news - Nyhetsverdig', '4news - Nyhetsverdig', '4news - Ikke nyhetsverdig', '4news - Nyhetsverdig', '3news - Ikke nyhetsverdig', '3news - Nyhetsverdig', '3news - Ikke nyhetsverdig', '3news - Ikke nyhetsverdig', '3news - Ikke nyhetsverdig', '3news - Ikke nyhetsverdig', '4news - Nyhetsverdig', '4news - Nyhetsverdig', '4news - Nyhetsverdig', '4news - Nyhetsverdig', '4news - Ikke nyhetsverdig', '4news - Nyhetsverdig', '3news - Ikke nyhetsverdig', '3news - Ikke nyhetsverdig', '3news - Ikke nyhetsverdig', '3news - Ikke nyhetsverdig', '3news - Ikke nyhetsverdig', '3news - Ikke nyhetsverdig', '4news - Ikke nyhetsverdig', '4news - Nyhetsverdig', '4news - Nyhetsverdig', '4news - Nyhetsverdig', '4news - Nyhetsverdig', '4news - Ikke nyhetsverdig']


# Konverter de tekstuelle beskrivelsene til numeriske klasser
y_true = []
y_pred = []

for entry in data2:
    parts = entry.split(' - ')
    #if parts[0] in ['0news', '2news']:
    if parts[0] in '3news':
        if parts[1] == 'Ikke nyhetsverdig':
            y_true.append(0)  # True label: Ikke nyhetsverdig
            y_pred.append(0)  # Predicted label: Ikke nyhetsverdig (TN)
        else:
            y_true.append(0)  # True label: Ikke nyhetsverdig
            y_pred.append(1)  # Predicted label: Nyhetsverdig (FP)
    #elif parts[0] == '1news':
    elif parts[0] == '4news':
        if parts[1] == 'Ikke nyhetsverdig':
            y_true.append(1)  # True label: Nyhetsverdig
            y_pred.append(0)  # Predicted label: Ikke nyhetsverdig (FN)
        else:
            y_true.append(1)  # True label: Nyhetsverdig
            y_pred.append(1)  # Predicted label: Nyhetsverdig (TP)

# Opprett forvirringsmatrisen
cm = confusion_matrix(y_true, y_pred)

# Beregn nøyaktighet og andre metrikker
total_vurderinger = len(y_true)
riktige_vurderinger = np.trace(cm)
feilvurderinger = total_vurderinger - riktige_vurderinger
accuracy = (riktige_vurderinger / total_vurderinger) * 100

# Print resultatene
print(f'TOTALE VURDERINGER: {total_vurderinger}')
print(f'TOTALT ANTALL RIKTIGE VURDERTE: {riktige_vurderinger}')
print(f'TOTALT ANTALL FEILVURDERTE: {feilvurderinger}')
print(f'TOTAL ACCURACY: {accuracy:.2f} %')

# Plot forvirringsmatrisen med matplotlib og seaborn
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Ikke nyhetsverdig', 'Nyhetsverdig'], yticklabels=['Ikke nyhetsverdig', 'Nyhetsverdig'])
plt.xlabel('Predicted')
plt.ylabel('True')
plt.title('Forvirringsmatrise - ny data')
#plt.title('Forvirringsmatrise - Iterasjon 4.1.23')
plt.show()