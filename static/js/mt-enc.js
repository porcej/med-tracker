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
            label: 'Age',
            name: 'age'
        },
        {
            label: 'Sex',
            name: 'sex',
            type: 'select',
            options: [
                { label: '', value: '' },
                { label: 'Male', value: 'Male' },
                { label: 'Female', value: 'Female' },
                { label: 'Other', value: 'Other' },
            ]
        },
        {
            label: 'Race Partipant',
            name: 'runner_type',
            type: 'select',
            options: [
                { label: 'Runner', value: 'Runner' },
                { label: 'Civilian', value: 'Civilian'},
                { label: 'Volunteer', value: 'Volunteer'},
                { label: 'Military', value: 'Military'}
            ]
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
            label: 'Primary Complaint',
            name: 'presentation',
            type: 'select',
            options: [
                { label: '', value: ''  },
                { label: 'Allergic Rxn', value: 'Allergic Rxn' },
                { label: 'Insect/ Bee', value: 'Insect/ Bee' },
                { label: 'Breathing Problem', value: 'Breathing Problem' },
                { label: 'Asthma', value: 'Asthma' },
                { label: 'Feeling Ill', value: 'Feeling Ill' },
                { label: 'Vision Issues', value: 'Vision Issues' },
                { label: 'Chest Discomfort', value: 'Chest Discomfort' },
                { label: 'Dysrhythmia', value: 'Dysrhythmia' },
                { label: 'Blister', value: 'Blister' },
                { label: 'Abrasion', value: 'Abrasion' },
                { label: 'Onychoptosis', value: 'Onychoptosis' },
                { label: 'Wound', value: 'Wound' },
                { label: 'Sprain/Strain', value: 'Sprain/Strain' },
                { label: 'Contusion', value: 'Contusion' },
                { label: 'Tendonitis', value: 'Tendonitis' },
                { label: 'Fracture', value: 'Fracture' },
                { label: 'Dizziness', value: 'Dizziness' },
                { label: 'Nausea/ Vomiting', value: 'Nausea/ Vomiting' },
                { label: 'Fatigue/ Weakness', value: 'Fatigue/ Weakness' },
                { label: 'MM Cramps', value: 'MM Cramps' },
                { label: 'Dehydration', value: 'Dehydration' },
                { label: 'Exertional Collapse', value: 'Exertional Collapse' },
                { label: 'Headache', value: 'Headache' },
                { label: 'Diarrhea', value: 'Diarrhea' },
                { label: 'Alterned MS', value: 'Alterned MS' },
                { label: 'Heat Exhaustion', value: 'Heat Exhaustion' },
                { label: 'Heat Stroke', value: 'Heat Stroke' },
                { label: 'Hyponatremia', value: 'Hyponatremia' },
                { label: 'Hypoglycemia', value: 'Hypoglycemia' },
                { label: 'Extremity Edema', value: 'Extremity Edema' },
                { label: 'Numbness', value: 'Numbness' },
                { label: 'Hypothermia', value: 'Hypothermia' },
                { label: 'Other - Specify in notes', value: 'Other' }
                // { label: 'Allergic Rxn', value: 'Ax' },
                // { label: 'Insect/ Bee', value: 'Ib' },
                // { label: 'Breathing Problem', value: 'Br' },
                // { label: 'Asthma', value: 'As' },
                // { label: 'Feeling Ill', value: 'FI' },
                // { label: 'Vision Issues', value: 'VI' },
                // { label: 'Chest Discomfort', value: 'CD' },
                // { label: 'Dysrhythmia', value: 'Dh' },
                // { label: 'Blister', value: 'B' },
                // { label: 'Abrasion', value: 'A' },
                // { label: 'Onychoptosis', value: 'Oy' },
                // { label: 'Wound', value: 'W' },
                // { label: 'Sprain/Strain', value: 'S' },
                // { label: 'Contusion', value: 'C' },
                // { label: 'Tendonitis', value: 'T' },
                // { label: 'Fracture', value: 'F' },
                // { label: 'Dizziness', value: 'Dz' },
                // { label: 'Nausea/ Vomiting', value: 'NV' },
                // { label: 'Fatigue/ Weakness', value: 'FW' },
                // { label: 'MM Cramps', value: 'MC' },
                // { label: 'Dehydration', value: 'D' },
                // { label: 'Exertional Collapse', value: 'EC' },
                // { label: 'Headache', value: 'Ha' },
                // { label: 'Diarrhea', value: 'Dr' },
                // { label: 'Alterned MS', value: 'aMS' },
                // { label: 'Heat Exhaustion', value: 'HE' },
                // { label: 'Heat Stroke', value: 'HS' },
                // { label: 'Hyponatremia', value: 'HN' },
                // { label: 'Hypoglycemia', value: 'LS' },
                // { label: 'Extremity Edema', value: 'EE' },
                // { label: 'Numbness', value: 'Nb' },
                // { label: 'Hypothermia', value: 'LT' },
                // { label: 'Other:', value: 'zzz' }
            ]
        },
        {
            label: 'Disposition',
            name: 'disposition',
            type: 'select',
            options: [
                { label: '', value: ''  },
                { label: 'Transport to Georgetown', value: 'Transport to Georgetown' },
                { label: 'Transport to George Washington', value: 'Transport to George Washington' },
                { label: 'Transport to Howard', value: 'Transport to Howard' },
                { label: 'Transport to Washington Hosp Ctr', value: 'Transport to Washington Hosp Ctr' },
                { label: 'Transport to INOVA Fairfax', value: 'Transport to INOVA Fairfax' },
                { label: 'Transport to INOVA Alexandria', value: 'Transport to INOVA Alexandria' },
                { label: 'Transport to VA Hosp Ctr', value: 'Transport to VA Hosp Ctr' },
                { label: 'Transport to Other', value: 'Transport to Other' },
                { label: 'Release to Resume Race', value: 'Release to Resume Race' },
                { label: 'Released Awaiting Bus', value: 'Released Awaiting Bus' },
                { label: 'Released Finished Race', value: 'Released Finished Race' },
                { label: 'Released LEft Course', value: 'Released LEft Course' },
                { label: 'Refused Trasnport', value: 'Refused Trasnport' },
                { label: 'Left Against Medical Advice', value: 'Left Against Medical Advice' },
                { label: 'Other Disposition - Specify in notes', value: 'Other Disposition' }
                // { label: 'Transport to Georgetown', value: 'TGT' },
                // { label: 'Transport to George Washington', value: 'TGW' },
                // { label: 'Transport to Howard', value: 'THH' },
                // { label: 'Transport to Washington Hosp Ctr', value: 'HWH' },
                // { label: 'Transport to INOVA Fairfax', value: 'TFX' },
                // { label: 'Transport to INOVA Alexandria', value: 'TAH' },
                // { label: 'Transport to VA Hosp Ctr', value: 'TVH' },
                // { label: 'Transport to Other', value: 'TOF' },
                // { label: 'Release to Resume Race', value: 'RRR' },
                // { label: 'Released Awaiting Bus', value: 'RAB' },
                // { label: 'Released Finished Race', value: 'RFR' },
                // { label: 'Released LEft Course', value: 'RLC' },
                // { label: 'Refused Trasnport', value: 'RT' },
                // { label: 'Left Against Medical Advice', value: 'AMA' },
                // { label: 'Other Disposition', value: 'OD' }
            ]
        },
        // {
        //     label: 'Transport Hospital',
        //     name: 'hospital',
        //     type: 'select',
        //     options: [
        //         { label: 'Not Trasnported', value: '' },
        //         { label: 'Alexandria Hospital', value: 'Alexandria Hospital' },
        //         { label: 'Inova Alexandria Hospital', value: 'Inova Alexandria Hospital' },
        //         { label: 'Inove Fairfax Hospital', value: 'Inove Fairfax Hospital' },
        //         { label: 'VHC Health Alrington', value: 'VHC Health Alrington' },
        //         { label: 'Childrens National Medical Center', value: 'Childrens National Medical Center' },
        //         { label: 'George Washington University Hospital', value: 'George Washington University Hospital' },
        //         { label: 'Hospital for Sick Children', value: 'Hospital for Sick Children' },
        //         { label: 'Howard University Hospital', value: 'Howard University Hospital' },
        //         { label: 'MedStar Georgetown University Hospital', value: 'MedStar Georgetown University Hospital' },
        //         { label: 'MedStar National Rehabilitation Hospital', value: 'MedStar National Rehabilitation Hospital' },
        //         { label: 'MedStar Washington Hospital Center', value: 'MedStar Washington Hospital Center' },
        //         { label: 'Psychiatric Institute of Washington', value: 'Psychiatric Institute of Washington' },
        //         { label: 'Sibley Memorial Hospital', value: 'Sibley Memorial Hospital' },
        //         { label: 'Specialty Hospital of Washington - Capitol Hill', value: 'Specialty Hospital of Washington - Capitol Hill' },
        //         { label: 'Specialty Hospital of Washington - Hadley', value: 'Specialty Hospital of Washington - Hadley' },
        //         { label: 'St. Elizabeths Hospital', value: 'St. Elizabeths Hospital' },
        //         { label: 'United Medical Center', value: 'United Medical Center' },
        //         { label: 'Washington DC Veterans Affairs Medical Center', value: 'Washington DC Veterans Affairs Medical Center' },
        //         { label: 'Other - add to note', value: 'Other' }
        //     ]
        // },
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
        { data: 'presentation', },
        { data: 'disposition' },
        { data: 'aid_station' }
    ],
    dom: 'Bfrtip',
    select: {
        style: 'os',
        selector: 'td:not(:last-child)' // no row selection on last column
    },
}); 

});