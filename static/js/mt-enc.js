// Main / parent / top level Editor
let encounterTable;
const encounterEditor = new DataTable.Editor({
    ajax: './api/encounters'.concat(window.current_aid_station_path),
    table: '#encounters-table',
    idSrc: 'id',
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
            ]
        },
        {
            label: 'Vitals',
            name: 'vitals',
            fieldInfo: 'List of Vital Signs, by time, please use [TIME TEMP RESP PULSE BP Meds, Fluids, Rx'
        },
        {
            label: "IV Provided",
            name: "iv",
            type: 'select',
            options: [
                { label: 'None', value: ''  },
                { label: 'Right Arm', value: 'Right Arm' },
                { label: 'Left Arm', value: 'Left Arm' },
                { label: 'Other - Specify in notes', value: 'Other' }
            ]
        },
        {
            label: 'Na+',
            name: 'na',
            fieldInfo: 'BMP - Sodium'
        },
        {
            label: 'K+',
            name: 'kplus',
            fieldInfo: 'BMP - Potassium'
        },
        {
            label: 'Cl-',
            name: 'cl',
            fieldInfo: 'BMP - Chlorine'
        },
        {
            label: 'tCO2',
            name: 'tco',
            fieldInfo: 'BMP - Bicarbonate'
        },
        {
            label: 'BUN',
            name: 'bun',
            fieldInfo: 'BMP - Blood Urea Nitrogen'
        },
        {
            label: 'Cr',
            name: 'cr',
            fieldInfo: 'BMP - Creatinine'
        },
                {
            label: 'Glu',
            name: 'glu',
            fieldInfo: 'BMP - Blood Glucose'
        },
        {
            label: 'Treatments',
            name: 'treatments',
            type: "textarea",
            fieldInfo: 'List treatment(s) provided, including use of ice, stretches, wound care, and physical therapy along with any other pertinent information.'
        },
        {
            label: 'Disposition',
            name: 'disposition',
            type: 'select',
            options: [
                { label: '', value: ''  },

                // Marine Corps Marathon Encounter
                { label: 'Transport to Georgetown', value: 'Transport to Georgetown' },
                { label: 'Transport to George Washington', value: 'Transport to George Washington' },
                { label: 'Transport to Howard', value: 'Transport to Howard' },
                { label: 'Transport to Washington Hosp Ctr', value: 'Transport to Washington Hosp Ctr' },
                { label: 'Transport to INOVA Fairfax', value: 'Transport to INOVA Fairfax' },
                { label: 'Transport to INOVA Alexandria', value: 'Transport to INOVA Alexandria' },
                { label: 'Transport to VA Hosp Ctr', value: 'Transport to VA Hosp Ctr' },

                // Run with the Maries Medical Encounter
                { label: 'Transport to Mary Washington', value: 'Transport to Mary Washington' },
                { label: 'Transport to Sentara NOVA', value: 'Transport to Sentara NOVA' },
                { label: 'Transport to Stafford', value: 'Transport to Stafford' },
                { label: 'Transport to Ft Belvoir', value: 'Transport to Ft Belvoir' },
                { label: 'Transport to Naval Clinic Quantico', value: 'Transport to Naval Clinic Quantico' },
                { label: 'Transport to INOVA Alexandria', value: 'Transport to INOVA Alexandria' },
                { label: 'Transport to Spotsylvania Regional', value: 'Transport to Spotsylvania Regional' },

                // Common Dispositions
                { label: 'Transport to Other - Specify in notes', value: 'Transport to Other' },
                { label: 'Release to Resume Race', value: 'Release to Resume Race' },
                { label: 'Released Awaiting Bus', value: 'Released Awaiting Bus' },
                { label: 'Released Finished Race', value: 'Released Finished Race' },
                { label: 'Released Left Course', value: 'Released Left Course' },
                { label: 'Refused Trasnport', value: 'Refused Trasnport' },
                { label: 'Left Against Medical Advice', value: 'Left Against Medical Advice' },
                { label: 'Other Disposition - Specify in notes', value: 'Other Disposition' }
            ]
        },
        {
            label: 'Notes',
            name: 'notes',
            type: "textarea",
        },
        { 
            label: 'Aid Station',
            name: 'aid_station',
            type: 'select', 
            options: window.current_aid_station_options
        }        
    ]
});
 
// Encounters DataTable shown in the page
encounterTable = new DataTable('#encounters-table', {
    idSrc: 'id',
    ajax: './api/encounters'.concat(window.current_aid_station_path),
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
    layout: {
        topStart: {
            buttons: [
                { extend: 'create', editor: encounterEditor },
                { extend: 'edit', editor: encounterEditor },
                { extend: 'remove', editor: encounterEditor }
            ]
        }
    },
    select: {
        style: 'single'
    }
});


// Encounters DataTable shown in the page
let participantsTable = new DataTable('#participants-table', {
    idSrc: 'id',
    ajax: './api/participants/',
    columns: [
        { data: 'bib' },
        { data: 'first_name' },
        { data: 'last_name' },
        { data: 'age', searchable: false, targets: 0 },
        { data: 'sex', },
    ],
    select: {
        style: 'single'
    }
});

$(document).ready(function () {   
    // let table = $('#participants-table').DataTable();
    $('#participants-table tbody').on('click', 'tr', function () {
        const row = participantsTable.row(this).data();
        encounterEditor
            .create()
            .title(`New Encounter with ${row.last_name}, ${row.first_name}`);
        encounterEditor.field('bib').set(row.bib)
        encounterEditor.field('first_name').set(row.first_name)
        encounterEditor.field('last_name').set(row.last_name)
        encounterEditor.field('age').set(row.age)
        encounterEditor.field('sex').set(row.sex)
        encounterEditor.field('runner_type').set('Runer')
        encounterEditor.open();
    });
});
