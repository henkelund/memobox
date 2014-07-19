/*$( window ).scroll(function() {
	refreshDate();
});	        

var previousYears = new Array(); 
var previousMonths = new Array(); 
var previousDates = new Array(); 
var lastYear = null;
var lastMonth = null;
var lastDate = null;*/

function stopVideo() {
	$("#moddalVideoContainer").html('<video id="modalVideo" style="display: none;" width="520" height="520" controls="controls" autoplay="autoplay"><source id="modalSource" src="" type="video/mp4" /></video>');
	$("#modalVideo > source").attr("src", "");
	$("#modalVideo").load();

}

function downloadFile() {
	window.open($("#originalImage").attr("src"),'_blank');
}

function hideFile() {
	var file_id = $("#filesDetailModalLabel").attr("file");
	$.get( "/files/hide?id="+file_id, function( data ) {
	  if(data == "ok") {
		  $("#"+file_id).parent().hide();
	  }
	});
	$('#filesDetailModal').modal('hide');
}

/*function showDate( dd ) {
	var counter = 0;
	var targetDate = new Date(lastYear, lastMonth, dd);
	$(".thumbnails .image").each(function( index ) {
		var time = new Date($( this ).attr("timestamp")*1000);
		
		if(time.getFullYear() == targetDate.getFullYear() && time.getMonth() == targetDate.getMonth() && time.getDate() == targetDate.getDate()) {
			//alert($( this ).position().top);
			//$("body").scrollTo($( this ));
			window.scrollTo(0, $( this ).position().top-65);
			exit;
		}
		counter++;
    });
}

function goToByScroll(id){
    $('html,body').animate({
        scrollTop: id.offset().top});
}

var selectedDevice = -1; 

function setDevice(id) {
	selectedDevice = id; 
}

function refreshDate() {
  var counter = 0; 
  $(".thumbnails .image:in-viewport").each(function( index ) {
  	  if(counter == 0) {
		  var time = new Date($( this ).attr("timestamp")*1000);
		  var viewMonth = time.getMonth();
		  var viewYear = time.getFullYear().toString();
		  var viewDate = time.getDate();
		  //var viewDate = time.getDate();
		  
		  if(lastDate != viewDate) {
		  	  if($.inArray(viewDate, previousDates) == -1) {
		      	previousDates.push(viewDate);					  	  
		  	  }
		  	  
		  	  lastDate = viewDate; 
		  }

		  if(lastMonth != viewMonth) {
		  	  if($.inArray(viewDate, previousMonths) == -1) {
		      	previousMonths.push(viewMonth);					  	  
		  	  }
		  	  
		  	  lastMonth = viewMonth; 
		  }

		  if(lastYear != viewYear) {
		  	  if($.inArray(viewYear, previousYears) == -1) {
		      	previousYears.push(viewYear);					  	  
		  	  }
		  	  
		  	  lastYear = viewYear; 
		  }

		  
		  var month = Array("January","February","March","April","May","June","July","August","September","October","November","December");
		  var yearList = "";
		  var monthList = "";
		  var dateList = "";

		  for (var i=0;i<previousDates.length;i++) {
			  dateList += "<li><a href='javascript:showDate("+previousDates[i]+")'>"+previousDates[i]+"</li>"; 
		  }
		  				  
		  for (var i=0;i<previousMonths.length;i++) {
			  monthList += "<li><a href='javascript:void(0)'>"+month[previousMonths[i]]+"</li>"; 
		  }

		  for (var i=0;i<previousYears.length;i++) {
			  yearList += "<li><a href='javascript:void(0)'>"+previousYears[i]+"</li>"; 
		  }
		  
		  $("#dateHolder").html("<ul class='nav'><li class='dropdown'><a class='dropdown-toggle ng-binding' data-toggle='dropdown' href='#'>"+viewDate+" <b style='border-top: 4px solid #fc423a;' class='caret'></b></a><ul id='dropdown-dates' class='dropdown-menu'>"+dateList+"</ul></li><li class='dropdown'><a  class='dropdown-toggle ng-binding' data-toggle='dropdown' href='#'>" + month[viewMonth]+" <b style='border-top: 4px solid #fc423a;' class='caret'></b></a><ul id='dropdown-dates' class='dropdown-menu'>"+monthList+"</ul></li><li class='dropdown'><a  class='dropdown-toggle ng-binding' data-toggle='dropdown' href='#'>"+viewYear+" <b style='border-top: 4px solid #fc423a;' class='caret'></b></a><ul id='dropdown-dates' class='dropdown-menu'>"+yearList+"</ul></li></ul>");
		  counter++;
		  $("#dateHolder").css("visibility","visible");
	  }
  });
}

setTimeout("refreshDate()", 500);*/

var uploadComplete = false; 
var progressInterval; 
			
$( document ).ready(function() {
	loadCloudBackupProgress();
	progressInterval = setInterval(function(){loadCloudBackupProgress()}, 10000);
});

function loadCloudBackupProgress() {
	if(!uploadComplete && browserStatus >= 0) {
		$.getJSON( "/lastping", function( data ) {
		  var items = [];
		  $.each( data, function( key, val ) {
		    items[key] = val; //.push( "<li id='" + key + "'>" + val + "</li>" );
		  });
		 
		  var remote_devicecount = items["remote_devicecount"];
		  var devicecount = items["devicecount"];
		  var progress = Math.round((remote_devicecount/devicecount)*100);
		  $("#cloudbackupprogress").html(progress+"%");
		  $("#cloudbackupprogress").attr("aria-valuenow", progress);
		  
		  if(remote_devicecount == 0 && devicecount == 0) {
			  clearInterval(progressInterval);
			  $("#progressContainer").hide();
			  
		  } else if (progress >= 100) {
			  uploadComplete = true; 
			  clearInterval(progressInterval);
			  $("#progressContainer").show();
			  $("#progressContainer").css("padding-top", "20px");
			  $("#progressContainer").html('<a style="color: white;" id="modalDownload" href="#"><span class="icon-white icon-check"></span> All of your data is now safe in the cloud.</a>');
		  } else {
			  var progressWidth = 15; 
			  if(progressWidth > 15) {
				  progressWidth = progress;
			  }
			  
			  $("#cloudbackupprogress").css("width", progressWidth+"%");
			  $("#progressContainer").show();
			  if (!window.matchMedia || (window.matchMedia("(min-width: 767px)").matches)) {
			  	$(".progress").attr("title", "There are <b>"+items["devicecount"]+"</b> files on your backupbox, of which <b>"+items["remote_devicecount"]+"</b> have been uploaded to the cloud so far. There are <b>"+(items["devicecount"]-items["remote_devicecount"])+"</b> files left to transfer.");
                $(".progress").tooltip();
            }					  
		  }					  
		});
	}
}

var lastTimstamp = Math.pow(2, 53); 
var lastMonth = -1; 
var lastYear = -1; 

function resetDate() {
	lastTimstamp = Math.pow(2, 53); 
	lastMonth = -1; 
	lastYear = -1; 
}

function parseDate() {
	var counter = 0; 
	var _months = Array("January","February","March","April","May","June","July","August","September","October","November","December");
	var firstLeft = -1; 

	$(".thumbnails .image").each(function( index ) {
		if(counter == 0)
			firstLeft = $( this ).position().left;
			
		var time = new Date($( this ).parent().attr("timestamp")*1000);
		var viewMonth = String(_months[time.getMonth()]).substr(0, 3);
		var viewYear = time.getFullYear().toString();
		var viewDate = time.getDate();

		if(counter == 3) {
			//alert(time.getTime() + " /// " + lastTimstamp);
		}

		if(time.getTime() < lastTimstamp && lastMonth != viewMonth) {
			alert(time.getTime() + " /// " + lastTimstamp);
			$( this ).append('<div class="dateHolder" style="left: '+(firstLeft - $( this ).position().left - 90)+'px; top: 0px; "><div class="month">'+viewMonth + '</div><div class="year">' + viewYear +'</div></div>');
			lastTimstamp = time.getTime(); 
			lastMonth = viewMonth;
			lastYear = viewYear;
		}
		
		counter++;
	})
}

//alert($(".thumbnails .image:in-viewport").first().attr("timestamp"));