var department = "";
var professor = "";
var attribute = "";
var level = "";
var query = "";

var department_call;
var course_call;
var professor_call;
var attribute_call;
var level_call;

$(document).ready(function() {
  $(window).keydown(function(event){
    if(event.keyCode == 13) {
      event.preventDefault();
      return false;
    }
  });

  $.ajax({
    url: '/term',
    contentType: 'application/json;charset=UTF-8',
    type: 'GET',
    dataType: "json",
    success: function(response) {
      var option = document.createElement("option");
      option.text = "No Term Specified";
      option.value = "";
      var select = document.getElementById("term");
      select.appendChild(option);
      if (response.data !== ""){
        for (k in response.data){
          for (j in response.data[k]){
            var option = document.createElement("option");
            option.text = response.data[k][j];
            option.value = j;
            var select = document.getElementById("term");
            select.appendChild(option);
          }
        }
        console.log(response);
      }
    },
    error: function(error) {
      console.log(error);
    }
  });
});

;(function($){
  $.fn.extend({
    donetyping: function(callback,timeout){
            timeout = timeout || 250; // 1 second default timeout
            var timeoutReference,
            doneTyping = function(el){
              if (!timeoutReference) return;
              timeoutReference = null;
              callback.call(el);
            };
            return this.each(function(i,el){
              var $el = $(el);
              $el.is(':input') && $el.on('keyup keypress paste',function(e){
                if (e.type=='keyup' && e.keyCode!=8) return;
                if (timeoutReference) clearTimeout(timeoutReference);
                timeoutReference = setTimeout(function(){
                  doneTyping(el);
                }, timeout);
              }).on('blur',function(){
                doneTyping(el);
              });
            });
          }
        });
})(jQuery);

$('#term').on('change', function() {
  searchQuery();
});

var searchQuery = function() {
  var a = $("#search").val();
  var input = {"search" : a.toString()};

  var e = document.getElementById("term");
  var term = e.options[e.selectedIndex].value;

  $("#course-description").html("");
  $("#course-sections").html("");
  $("#course-terms").html("");

  $("#course").html("");
  $("#course-top").html("");
  $("#department").html("");
  $("#professor").html("");
  $("#attribute").html("");
  $("#level").html("");

  if (course_call){
    course_call.abort();
  }
  if (department_call){
    department_call.abort();
  }
  if (attribute_call){
    attribute_call.abort();
  }
  if (level_call){
    level_call.abort();
  }
  if (professor_call){
    professor_call.abort();
  }

  query = 'search=' + a + '&department=' + department + '&professor=' + professor + '&attribute=' + attribute + '&level=' + level + '&term=' + term;

  course_call = $.ajax({
    url: '/search-course?' + query,
    contentType: 'application/json;charset=UTF-8',
    type: 'GET',
    dataType: "json",
    success: function(response) {
      if (response.data !== ""){

        var coursePosition = "#course";
        if (department !== "" || professor !== "" || attribute !== ""){
          coursePosition = "#course-top";
        }

        $(coursePosition).html("");
        $(coursePosition).append("<h2>Course</h2>"); 
        for (var i = 0; i < response.data.course.length; i++) { 
          $(coursePosition).append("<a href= '#' onclick='openCourseDescription(\"" + response.data.link[i] + "\")'>" + response.data.course[i] + "</a>");
          $(coursePosition).append("&emsp;");
          if (term !== "") {
            $(coursePosition).append("<a href= '#' onclick='openCourseSections(\"" + response.data.section[i] + "\")'>Section</a>");
            $(coursePosition).append("&emsp;");
          }
          $(coursePosition).append("<a href= '#' onclick='openCourseTerms(\"" + response.data.terms[i] + "\")'>Terms</a>");
          $(coursePosition).append("</br>");
        }
        console.log(response);
      }
    },
    error: function(error) {
      console.log(error);
    }
  });

department_call = $.ajax({
  url: '/search-department?' + query,
  contentType: 'application/json;charset=UTF-8',
  type: 'GET',
  dataType: "json",
  success: function(response) {
   if (response.data !== ""){
    $("#department").html("");
    $("#department").append("<h2>Department</h2>"); 
    for (var i = 0; i < response.data.name.length; i++) { 
      $("#department").append("<a href= '#' onclick='saveDepartment(\"" + response.data.link[i] + "\")'>" + response.data.name[i] + "</a>");
      $("#department").append("</br>");

      
    }
    console.log(response);
  }
},
error: function(error) {
  console.log(error);
}
});

professor_call = $.ajax({
  url: '/search-professor?' + query,
  contentType: 'application/json;charset=UTF-8',
  type: 'GET',
  dataType: "json",
  success: function(response) {
    if (response.data !== "" && response.data.name !== null){
      $("#professor").html("");
      $("#professor").append("<h2>Professor</h2>");
      for (var i = 0; i < response.data.name.length; i++) {
        $("#professor").append("<a href= '#' onclick='saveProfessor(\"" + response.data.link[i] + "\")'>" + response.data.name[i] + "</a>");
        $("#professor").append("</br>");
      }
      console.log(response);
    }
  },
  error: function(error) {
    console.log(error);
  }
});

attribute_call = $.ajax({
  url: '/search-attribute?' + query,
  contentType: 'application/json;charset=UTF-8',
  type: 'GET',
  dataType: "json",
  success: function(response) {
   if (response.data !== ""){
    $("#attribute").html("");
    $("#attribute").append("<h2>Attribute</h2>"); 
    for (var i = 0; i < response.data.length; i++) { 
      $("#attribute").append("<a href= '#' onclick='saveAttribute(\"" + response.data[i] + "\")'>" + response.data[i] + "</a>");
      $("#attribute").append("</br>");
    }
    console.log(response);
  }
},
error: function(error) {
  console.log(error);
}
});

level_call = $.ajax({
  url: '/search-level?' + query,
  contentType: 'application/json;charset=UTF-8',
  type: 'GET',
  dataType: "json",
  success: function(response) {
   if (response.data !== ""){
    $("#level").html("");
    $("#level").append("<h2>Level</h2>"); 
    for (var i = 0; i < response.data.length; i++) { 
      $("#level").append("<a href= '#' onclick='saveLevel(\"" + response.data[i] + "\")'>" + response.data[i] + "</a>");
      $("#level").append("</br>");
    }
    console.log(response);
  }
},
error: function(error) {
  console.log(error);
}
});
};

function saveDepartment(name){
  department = name;
  $('#search').val('');
  searchQuery();
  $("#savedDepartment").html("<a href= '#' onclick='clearDepartment()'> Remove " + name + "</a>"); 
  return false;
}

function clearDepartment(){
  department = "";
  $("#savedDepartment").html(""); 
  searchQuery();
  return false;
}

function saveLevel(name){
  level = name;
  $('#search').val('');
  searchQuery();
  $("#savedLevel").html("<a href= '#' onclick='clearLevel()'> Remove " + name + "</a>"); 
  return false;
}

function clearLevel(){
  level = "";
  $("#savedLevel").html(""); 
  searchQuery();
  return false;
}

function saveAttribute(name){
  attribute = name;
  $('#search').val('');
  searchQuery();
  $("#savedAttribute").html("<a href= '#' onclick='clearAttribute()'> Remove " + name + "</a>"); 
  return false;
}

function clearAttribute(){
  attribute = "";
  $("#savedAttribute").html(""); 
  searchQuery();
  return false;
}

function saveProfessor(name){
  professor = name;
  $('#search').val('');
  searchQuery();
  $("#savedProfessor").html("<a href= '#' onclick='clearProfessor()'> Remove " + name + "</a>"); 
  return false;
}

function clearProfessor(){
  professor = "";
  $("#savedProfessor").html(""); 
  searchQuery();
  return false;
}

function openCourseDescription(link){
  $.ajax({
    url: link,
    contentType: 'application/json;charset=UTF-8',
    type: 'GET',
    dataType: "json",
    success: function(response) {
      if (response.data !== ""){
        $("#course-description").html(JSON.stringify(response.data));
        console.log(response);
      }
    },
    error: function(error) {
      console.log(error);
    }
  });
  return false;
}

function openCourseSections(link){
  $.ajax({
    url: link,
    contentType: 'application/json;charset=UTF-8',
    type: 'GET',
    dataType: "json",
    success: function(response) {
      if (response.data !== ""){
        $("#course-sections").html(JSON.stringify(response.data));
        console.log(response);
      }
    },
    error: function(error) {
      console.log(error);
    }
  });
  return false;
}

function openCourseTerms(link){
  $.ajax({
    url: link,
    contentType: 'application/json;charset=UTF-8',
    type: 'GET',
    dataType: "json",
    success: function(response) {
      if (response.data !== ""){
        $("#course-terms").html(JSON.stringify(response.data));
        console.log(response);
      }
    },
    error: function(error) {
      console.log(error);
    }
  });
  return false;
}

$('#search')
.donetyping(searchQuery)
.click(function(){
  if ($("#search").val().length === 0 && !course_call  && !department_call && !attribute_call && !level_call && !professor_call){
    searchQuery();
  }
});
