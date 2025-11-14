(function() {
    'use strict';
    
    // Función para esperar a que jQuery esté disponible
    function waitForJQuery(callback) {
        if (window.jQuery) {
            callback(window.jQuery);
        } else if (typeof django !== 'undefined' && django.jQuery) {
            callback(django.jQuery);
        } else {
            setTimeout(function() {
                waitForJQuery(callback);
            }, 100);
        }
    }
    
    waitForJQuery(function($) {
        $(document).ready(function() {
            // Función para actualizar las opciones de columnas basadas en la tabla seleccionada
            function updateColumnChoices() {
                var tableId = $('#id_table').val();
                
                if (!tableId) {
                    return;
                }
                
                // Obtener todas las filas de columnas del inline
                $('.dynamic-report_columns').each(function() {
                    var row = $(this);
                    var columnSelect = row.find('select[name*="column"]');
                    
                    if (columnSelect.length === 0) {
                        return;
                    }
                    
                    var currentValue = columnSelect.val();
                    
                    // Hacer una petición AJAX para obtener las columnas de la tabla seleccionada
                    $.ajax({
                        url: '/admin/core/column/autocomplete/',
                        data: {
                            'table__id__exact': tableId,
                            'is_active__exact': 1,
                            'term': ''
                        },
                        dataType: 'json',
                        success: function(data) {
                            // Limpiar las opciones actuales (excepto la vacía)
                            columnSelect.find('option:not([value=""])').remove();
                            
                            // Agregar las nuevas opciones
                            $.each(data.results, function(index, item) {
                                var option = new Option(item.text, item.id, false, false);
                                columnSelect.append(option);
                            });
                            
                            // Restaurar el valor seleccionado si existe
                            if (currentValue && columnSelect.find('option[value="' + currentValue + '"]').length > 0) {
                                columnSelect.val(currentValue);
                            }
                        },
                        error: function(xhr, status, error) {
                            console.error('Error al cargar columnas:', error);
                        }
                    });
                });
            }
            
            // Ejecutar cuando cambie la tabla seleccionada
            $(document).on('change', '#id_table', function() {
                updateColumnChoices();
            });
            
            // Ejecutar al cargar la página si ya hay una tabla seleccionada
            setTimeout(function() {
                if ($('#id_table').val()) {
                    updateColumnChoices();
                }
            }, 500);
        });
    });
})();
