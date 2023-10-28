$(document).ready(function () {
$.fn.dataTable.ext.buttons.refresh = {
    text: 'Refresh'
  , action: function ( e, dt, node, config ) {
      dt.clear().draw();
      dt.ajax.reload();
    }
};

const editor = new DataTable.Editor({
    ajax: './api/encounters'.concat(window.current_aid_station_path),
    fields: [
        {
            label: 'Bib #',
            name: 'bib'
        },
        {
            label: 'First Name',
            name: 'first_name'
        },
        {
            label: 'Last Name',
            name: 'last_name'
        },
        {
            label: "Time into Aid Station",
            name: "time_in",
            type: 'datetime',
            format: 'HH:mm',
            fieldInfo: '24 hour clock (HH:mm)'
        },
        {
            label: 'Time out of Aid Station',
            name: 'time_out',
            type: 'datetime',
            format: 'HH:mm',
            fieldInfo: '24 hour clock (HH:mm)'
        },
        {
            label: 'Disposition',
            name: 'disposition',
            type: 'select',
            options: [
                { label:'Released to finsh race', value: 'Released to finsh race' },
                { label:'Released and left race', value: 'Released and left race' },
                { label:'Took Sweeper bus', value: 'Took Sweeper bus' },
                { label:'Transported by EMS', value: 'Transported by EMS' },
                { label:'Self Transport to hospital', value: 'Self Transport to hospital' }
            ]
        },
        {
            label: 'Transport Hospital',
            name: 'hospital',
            type: 'select',
            options: [
                { label:'Alexandria Hospital', value: 'Alexandria Hospital' },
                { label:'Inova Alexandria Hospital', value: 'Inova Alexandria Hospital' },
                { label:'Inove Fairfax Hospital', value: 'Inove Fairfax Hospital' },
                { label:'VHC Health Alrington', value: 'VHC Health Alrington' },
                { label:'Childrens National Medical Center', value: 'Childrens National Medical Center' },
                { label:'George Washington University Hospital', value: 'George Washington University Hospital' },
                { label:'Hospital for Sick Children', value: 'Hospital for Sick Children' },
                { label:'Howard University Hospital', value: 'Howard University Hospital' },
                { label:'MedStar Georgetown University Hospital', value: 'MedStar Georgetown University Hospital' },
                { label:'MedStar National Rehabilitation Hospital', value: 'MedStar National Rehabilitation Hospital' },
                { label:'MedStar Washington Hospital Center', value: 'MedStar Washington Hospital Center' },
                { label:'Psychiatric Institute of Washington', value: 'Psychiatric Institute of Washington' },
                { label:'Sibley Memorial Hospital', value: 'Sibley Memorial Hospital' },
                { label:'Specialty Hospital of Washington - Capitol Hill', value: 'Specialty Hospital of Washington - Capitol Hill' },
                { label:'Specialty Hospital of Washington - Hadley', value: 'Specialty Hospital of Washington - Hadley' },
                { label:'St. Elizabeths Hospital', value: 'St. Elizabeths Hospital' },
                { label:'United Medical Center', value: 'United Medical Center' },
                { label:'Washington DC Veterans Affairs Medical Center', value: 'Washington DC Veterans Affairs Medical Center' },
                { label:'Other - add to note', value: 'Other' }
            ]
        },
        {
            label: 'Notes',
            name: 'notes',
            type: "textarea"
        },
        { 
            label: 'Aid Station',
            name: 'aid_station',
            type: 'select', 
            options: window.current_aid_station_options
        }
    ],
    idSrc: 'id',
    table: '#encounters-table'
});
 
const table = new DataTable('#encounters-table', {
    ajax: './api/encounters'.concat(window.current_aid_station_path),
    buttons: [
        { extend: 'create', editor },
        { extend: 'edit', editor },
        { extend: 'remove', editor },
        { extend: 'refresh' },
        {
            extend: 'collection',
            text: 'Export',
            buttons: [
                {
                    extend: 'copy',
                    exportOptions: {
                        orthogonal: 'export'
                    }
                },
                {
                    extend: 'csv',
                    exportOptions: {
                        orthogonal: 'export'
                    }
                },
                {
                    extend: 'excel',
                    exportOptions: {
                        orthogonal: 'export'
                    }
                },
                {
                    extend: 'print',
                    exportOptions: {
                        orthogonal: 'export'
                    }
                }
            ]
        }
    ],
    columns: [
        { data: 'bib' },
        { data: 'first_name' },
        { data: 'last_name' },
        { data: 'time_in', },
        { data: 'time_out', },
        { data: 'disposition' },
        { data: 'hospital' },
        { data: 'notes' },
        { data: 'aid_station' }
    ],
    dom: 'Bfrtip',
    select: {
        style: 'os',
        selector: 'td:not(:last-child)' // no row selection on last column
    },
}); 

});